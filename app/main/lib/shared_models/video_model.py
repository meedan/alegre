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
from app.main import db
from app.main.model.video import Video

def _after_log(retry_state):
  app.logger.debug("Retrying video similarity...")

class VideoModel(SharedModel):
    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def save(self, video):
        saved_video = None
        try:
            # First locate existing video and append new context
            existing = db.session.query(Video).filter(Video.url==video.url).one()
            if existing:
                if video.hash_value and not existing.hash_value:
                    existing.hash_value = video.hash_value
                    flag_modified(existing, 'hash_value')
                if video.context not in existing.context:
                    if isinstance(video.context, list):
                        existing.context.append(video.context[0])
                    else:
                        existing.context.append(video.context)
                    flag_modified(existing, 'context')
                saved_video = existing
        except NoResultFound as e:
            # Otherwise, add new video, but with context as an array
            if video.context and not isinstance(video.context, list):
                video.context = [video.context]
            db.session.add(video)
            saved_video = video
        except Exception as e:
            db.session.rollback()
            raise e
        try:
            db.session.commit()
            return saved_video
        except Exception as e:
            db.session.rollback()
            raise e

    def get_tempfile(self):
        return tempfile.NamedTemporaryFile()

    def execute_command(self, command):
        return os.popen(command).read()

    def load(self):
        self.directory = app.config['PERSISTENT_DISK_PATH']
        self.ffmpeg_dir = "/usr/local/bin/ffmpeg"
        pathlib.Path(self.directory).mkdir(parents=True, exist_ok=True)

    def respond(self, task):
        app.logger.info('Received task that looks like: '+str(json.dumps(task)))
        if task["command"] == "delete":
            return self.delete(task)
        elif task["command"] == "add":
            return self.add(task)
        elif task["command"] == "search":
            return self.search(task)

    def delete(self, task):
        deleted = False
        filepath = None
        if 'doc_id' in task:
            videos = db.session.query(Video).filter(Video.doc_id==task.get("doc_id")).all()
            if videos:
                video = videos[0]
        elif 'url' in task:
            videos = db.session.query(Video).filter(Video.url==task.get("url")).all()
            if videos:
                video = videos[0]
        if video:
            filepath = self.tmk_file_path(video.folder, video.filepath)
            if task.get("context", {}) in video.context and len(video.context) > 1:
                deleted = drop_context_from_record(video, task.get("context", {}))
            else:
                if os.path.exists(filepath):
                    os.remove(filepath)
                deleted = db.session.query(Video).filter(Video.id==video.id).delete()
        return {"requested": task, "result": {"outfile": filepath, "deleted": deleted}}

    def overload_context_to_denote_content_type(self, task):
        return {**task, **{"context": {**task.get("context", {}), **{"content_type": "video"}}}}

    def add(self, task):
        try:
            temp_video_file = self.get_tempfile()
            remote_request = urllib.request.Request(task["url"], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(remote_request) as response, open(temp_video_file.name, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            tmk_file_output = tmkpy.hashVideo(temp_video_file.name,self.ffmpeg_dir)
            hash_value=tmk_file_output.getPureAverageFeature()
            video = Video(doc_id=task.get("doc_id"), url=task["url"], context=task.get("context", {}), hash_value=hash_value)
            video = self.save(video)
            tmk_file_output.writeToOutputFile(self.tmk_file_path(video.folder, video.filepath), self.tmk_program_name())
            if task.get("match_across_content_types", False):
                am = AudioModel('audio')
                am.add(self.overload_context_to_denote_content_type(task))
            return {"requested": task, "result": {"outfile": self.tmk_file_path(video.folder, video.filepath)}, "success": True}
        except urllib.error.HTTPError:
            return {"requested": task, "result": {"url": video.url}, "success": False}

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
            matches = db.session.execute(text(cmd), context_hash).fetchall()
            keys = ('id', 'doc_id', 'url', 'folder', 'filepath', 'context', 'hash_value')
            rows = [dict(zip(keys, values)) for values in matches]
            for row in rows:
                row["context"] = [c for c in row["context"] if context_matches(context, c)]
            return rows
        except Exception as e:
            db.session.rollback()
            raise e

    def search(self, task):
        context = {}
        video = None
        temporary = False
        if task.get('context'):
            context = task.get('context')
        if task.get('doc_id'):
            videos = db.session.query(Video).filter(Video.doc_id==task.get("doc_id")).all()
            if videos and not video:
                video = videos[0]
        elif task.get('url'):
            videos = db.session.query(Video).filter(Video.url==task.get("url")).all()
            if videos and not video:
                video = videos[0]
        if video is None:
            temporary = True
            if not task.get("doc_id"):
                task["doc_id"] = str(uuid.uuid4())
            self.add(task)
            videos = db.session.query(Video).filter(Video.doc_id==task.get("doc_id")).all()
            if videos and not video:
                video = videos[0]
        if video:
            matches = self.search_by_context(context)
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
            	scores = tmkpy.query(self.tmk_file_path(video.folder, video.filepath),files,1)
            except RuntimeError as e:
            	print(e)
            threshold = task.get("threshold", 0.0) or 0.0
            results = []
            for i,score in enumerate(scores):
                if score > threshold:
                    results.append({
                        "context": qualified_matches[i].get("context", {}),
                        "filename": files[i],
                        "score": score
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

    def tmk_file_path(self, folder, filepath, create_path=True):
        if create_path:
            pathlib.Path(f"{self.directory}/{folder}").mkdir(parents=True, exist_ok=True)
        return f"{self.directory}/{folder}/{filepath}.tmk"
        
    def get_fullpath_files(self, matches, check_exists=True):
        full_paths = []
        for match in matches:
            filename = self.tmk_file_path(match["folder"], match["filepath"], check_exists)
            if check_exists and os.path.exists(filename) or not check_exists:
                full_paths.append(filename)
        return full_paths
