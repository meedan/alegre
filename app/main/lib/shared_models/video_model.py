import time
import json
import uuid
import os
import tempfile
import pathlib
import urllib.error
import urllib.request
import shutil
import numpy as np
from scipy.spatial import distance
from flask import current_app as app
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import text
import tenacity
import tmkpy
from sqlalchemy.orm.exc import NoResultFound

from app.main.lib.shared_models.audio_model import AudioModel
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.similarity_helpers import get_context_query, drop_context_from_record
from app.main.lib.helpers import context_matches
from app.main.lib import media_crud
from app.main.lib.error_log import ErrorLog
from app.main.lib import media_crud
from app.main import db
from app.main.model.video import Video
from app.main.lib.presto import Presto
from app.main.lib.s3_client import download_file_from_s3

def _after_log(retry_state):
  app.logger.debug("Retrying video similarity...")

class VideoModel(SharedModel):
    def overload_context_to_denote_content_type(self, task):
        app.logger.error(f"input to overload_context_to_denote_content_type_v2 is {task}")
        return {**task, **{"context": {**task.get("context", {}), **{"content_type": "video"}}}}

    def delete(self, task):
        return media_crud.delete(task, Video)

    def add(self, task):
        hash_value = (task.get("result", {}) or {}).get("hash_value")
        s3_folder = (task.get("result", {}) or {}).get("folder")
        s3_filepath = (task.get("result", {}) or {}).get("filepath")
        if hash_value:
            task["hash_value"] = hash_value
        added, obj = media_crud.add(task, Video, ["hash_value", "folder", "filepath"])
        download_file_from_s3(s3_folder, s3_filepath, media_crud.tmk_file_path(obj.folder, obj.filepath))
        return added

    def blocking_search(self, task, modality):
        video, temporary, context, presto_result = media_crud.get_blocked_presto_response(task, Video, modality)
        video.hash_value = presto_result["body"]["hash_value"]
        if video:
            matches = self.search(task).get("result")
            if temporary:
                media_crud.delete(task, Video)
            else:
                media_crud.save(video, Video, ["hash_value"])
            if task.get("limit"):
                return {"result": matches[:task.get("limit")]}
            else:
                return {"result": matches}
        else:
            return {"error": "Video not found for provided task", "task": task}

    def async_search(self, task, modality):
        return media_crud.get_async_presto_response(task, Video, modality)

    def get_tempfile(self):
        return tempfile.NamedTemporaryFile()

    def execute_command(self, cmd, params):
      return db.session.execute(cmd, params).fetchall()

    def load(self):
        self.directory = app.config['PERSISTENT_DISK_PATH']
        pathlib.Path(self.directory).mkdir(parents=True, exist_ok=True)

    def respond(self, task):
        app.logger.info('Received task that looks like: '+str(json.dumps(task)))
        if task["command"] == "delete":
            return self.delete(task)
        elif task["command"] == "add":
            return self.add(task)
        elif task["command"] == "search":
            return self.search(task)

    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def search_by_context(self, context):
        try:
            context_query, context_hash = get_context_query(context)
            if context_query:
                cmd = """
                  SELECT id, doc_id, url, folder, filepath, context, hash_value FROM videos
                  WHERE 
                """+context_query
            else:
                cmd = """
                  SELECT id, doc_id, url, folder, filepath, context, hash_value FROM videos
                """
            matches = self.execute_command(text(cmd), context_hash)
            keys = ('id', 'doc_id', 'url', 'folder', 'filepath', 'context', 'hash_value')
            rows = [dict(zip(keys, values)) for values in matches]
            for row in rows:
                row["context"] = [c for c in row["context"] if context_matches(context, c)]
            return rows
        except Exception as e:
            db.session.rollback()
            raise e

    def search(self, task):
        body, threshold, limit = media_crud.parse_task_search(task)
        video, temporary = media_crud.get_object(body, Video)
        if video.hash_value is None:
            callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], "video")
            if task.get("doc_id") is    None:
                task["doc_id"] = str(uuid.uuid4())
            response = json.loads(Presto.send_request(app.config['PRESTO_HOST'], "video__Model", callback_url, task, False).text)
            # Warning: this is a blocking hold to wait until we get a response in 
            # a redis key that we've received something from presto.
            result = Presto.blocked_response(response, "video")
            video.hash_value = result.get("body", {}).get("result", {}).get("hash_value")
        if video:
            matches = self.search_by_context(body["context"])
            default_list = list(np.zeros(len(video.hash_value)))
            try:
                l1_scores = np.ndarray.flatten((1-distance.cdist([r.get("hash_value", default_list) or default_list for r in matches], [video.hash_value], 'cosine'))).tolist()
            except:
                app.logger.info('L1 scoring failed while running search for video id of '+str(video.id)+' match ids of : '+str([e.get("id") for e in matches]))
                l1_scores = [0.0 for e in matches]
            qualified_matches = []
            for i,match in enumerate(matches):
                if l1_scores[i] > app.config['VIDEO_MODEL_L1_SCORE']:
                    qualified_matches.append(match)
            files = self.get_fullpath_files(qualified_matches, False)
            try:
                scores = tmkpy.query(media_crud.tmk_file_path(video.folder, video.filepath),files,1)
            except Exception as err:
                ErrorLog.notify(err)
                raise err
            threshold = float(task.get("threshold", 0.0) or 0.0)
            results = []
            for i,score in enumerate(scores):
                if score > threshold:
                    results.append({
                        "context": qualified_matches[i].get("context", {}),
                        "folder": qualified_matches[i].get("folder"),
                        "filepath": qualified_matches[i].get("filepath"),
                        "doc_id": qualified_matches[i].get("doc_id"),
                        "url": qualified_matches[i].get("url"),
                        "filename": files[i],
                        "score": score,
                        "model": "video"
                    })
            if temporary:
                self.delete(task)
            limit = task.get("limit")
            if limit:
                return {"result": results[:limit]}
            else:
                return {"result": results}
        else:
            return {"error": "Video not found for provided task", "task": task}

    def tmk_program_name(self):
        return "AlegreVideoEncoder"

    def get_fullpath_files(self, matches, check_exists=True):
        full_paths = []
        for match in matches:
            filename = media_crud.tmk_file_path(match["folder"], match["filepath"], check_exists)
            if check_exists and os.path.exists(filename) or not check_exists:
                full_paths.append(filename)
        return full_paths
