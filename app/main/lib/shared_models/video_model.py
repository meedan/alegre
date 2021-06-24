import uuid
import os
import tempfile
import pathlib
import urllib.request
import shutil
from sentence_transformers import SentenceTransformer
from flask import current_app as app
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import text
import tenacity
from sqlalchemy.orm.exc import NoResultFound

from app.main.lib.shared_models.shared_model import SharedModel
from app.main import db
from app.main.model.video import Video

def _after_log(retry_state):
  app.logger.debug("Retrying video similarity...")

# task = {"doc_id":"Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8","url":"https://qa-assets.checkmedia.org/uploads/uploaded_video/538836/IMG_6828.MOV","context":{"team_id":4874,"project_media_id":554571,"has_custom_id":True}}
# task = {"doc_id":None,"url":"https://qa-assets.checkmedia.org/uploads/uploaded_video/538836/IMG_6828.MOV","context":{"team_id":4874,"project_media_id":554571,"has_custom_id":True}}
# from app.main.lib.shared_models.video_model import VideoModel
# vm = VideoModel("video")
# vm.load()
# vm.add(task)
# from app.main.lib.shared_models.video_model import VideoModel
# vm = VideoModel("video")
# vm.load()
# vm.search(task)
class VideoModel(SharedModel):
    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def save(self, video):
        saved_video = None
        try:
            # First locate existing video and append new context
            existing = db.session.query(Video).filter(Video.url==video.url).one()
            if video.context not in existing.context:
                existing.context.append(video.context)
                flag_modified(existing, 'context')
            saved_video = existing
        except NoResultFound as e:
            # Otherwise, add new video, but with context as an array
            if video.context:
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
        if task["command"] == "delete":
            return self.delete(task)
        elif task["command"] == "add":
            return self.add(task)
        elif task["command"] == "search":
            return self.search(task)

    def delete(self, task):
        if 'doc_id' in task:
            videos = db.session.query(Video).filter(Video.doc_id==task.get("doc_id")).all()
            if videos:
                video = videos[0]
        elif 'url' in task:
            videos = db.session.query(Video).filter(Video.url==task.get("url")).all()
            if videos:
                video = videos[0]
        filepath = self.tmk_file_path(video.folder, video.filepath)
        if os.path.exists(filepath):
            os.remove(filepath)
        deleted = db.session.query(Video).filter(Video.id==video.id).delete()
        return {"requested": task, "result": {"outfile": filepath, "deleted": deleted}}

    def add(self, task):
        video = Video(task.get("doc_id"), task["url"], task.get("context", {}))
        video = self.save(video)
        temp_video_file = self.get_tempfile()
        remote_request = urllib.request.Request(video.url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(remote_request) as response, open(temp_video_file.name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        outfile = self.tmk_file_path(video.folder, video.filepath)
        hash_video_command = self.tmk_hash_video_command()
        result = self.execute_command(f"{hash_video_command} -f {self.ffmpeg_dir} -i {temp_video_file.name} -o {outfile}")
        return {"requested": task, "result": {"outfile": outfile}}

    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def search_by_context(self, context):
        try:
            context_query, context_hash = self.get_context_query(context)
            if context_query:
                cmd = """
                  SELECT id, doc_id, url, folder, filepath, context FROM videos
                  WHERE 
                """+context_query
            else:
                cmd = """
                  SELECT id, doc_id, url, folder, filepath, context FROM videos
                """
            matches = db.session.execute(text(cmd), context_hash).fetchall()
            keys = ('id', 'doc_id', 'url', 'folder', 'filepath', 'context')
            return [dict(zip(keys, values)) for values in matches]
        except Exception as e:
            db.session.rollback()
            raise e

    def search(self, task):
        context = {}
        video = None
        if task.get('context'):
            context = task.get('context')
        elif task.get('url'):
            videos = db.session.query(Video).filter(Video.url==task.get("url")).all()
            if videos and not video:
                video = videos[0]
        if task.get('doc_id'):
            videos = db.session.query(Video).filter(Video.doc_id==task.get("doc_id")).all()
            if videos and not video:
                video = videos[0]
        elif task.get('url'):
            videos = db.session.query(Video).filter(Video.url==task.get("url")).all()
            if videos and not video:
                video = videos[0]
        if video:
            matches = self.search_by_context(context)
            temp_search_file = self.get_tempfile()
            temp_comparison_file = self.get_tempfile()
            with open(temp_search_file.name, 'w') as out_file:
                out_file.write(str.join("\n", self.get_fullpath_files(matches)))
            with open(temp_comparison_file.name, 'w') as out_file:
                out_file.write(self.tmk_file_path(video.folder, video.filepath))
            tmk_query_command = self.tmk_query_command()
            result = self.execute_command(f"{tmk_query_command} --c1 -1.0 --c2 0.0 {temp_search_file.name} {temp_comparison_file.name}")
            return {"result": self.parse_search_results(result, matches)}
        else:
            return {"error": "Video not found for provided task", "task": task}

    def get_context_query(self, context):
        context_query = []
        context_hash = {}
        for key, value in context.items():
            if key != "project_media_id":
                if isinstance(value, list):
                    context_clause = "("
                    for i,v in enumerate(value):
                        context_clause += "context @> '[{\""+key+"\": :context_"+key+"_"+str(i)+"}]'"
                        if len(value)-1 != i:
                            context_clause += " OR "
                        context_hash[f"context_{key}_{i}"] = v
                    context_clause += ")"
                    context_query.append(context_clause)
                else:
                    context_query.append("context @>'[{\""+key+"\": :context_"+key+"}]'")
                    context_hash[f"context_{key}"] = value
        return str.join(" AND ",  context_query), context_hash
    
    def tmk_dir(self):
        return "./threatexchange/tmk/cpp/"

    def tmk_query_command(self):
        return f"{self.tmk_dir()}tmk-query"

    def tmk_hash_video_command(self):
        return f"{self.tmk_dir()}tmk-hash-video"

    def tmk_file_path(self, folder, filepath):
        pathlib.Path(f"{self.directory}/{folder}").mkdir(parents=True, exist_ok=True)
        return f"{self.directory}/{folder}/{filepath}.tmk"
        
    def get_fullpath_files(self, matches):
        full_paths = []
        for match in matches:
            filename = self.tmk_file_path(match["folder"], match["filepath"])
            if os.path.exists(filename):
                full_paths.append(filename)
        return full_paths

    def get_match_dictionary(self, matches):
        match_dictionary = {}
        for match in matches:
            match_dictionary[self.tmk_file_path(match["folder"], match["filepath"])] = match
        return match_dictionary

    def parse_search_results(self, result, matches):
        results = []
        match_dictionary = self.get_match_dictionary(matches)
        for row in result.split("\n")[:-1]:
            level1, level2, first_file, second_file = row.split(" ")
            results.append({
                "context": match_dictionary[first_file]["context"],
                "score": level2,
                "filename": first_file,
            })
        return results