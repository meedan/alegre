import base64
import os
import tempfile
import pathlib
import urllib.request
import shutil
from sentence_transformers import SentenceTransformer
from flask import current_app as app

from app.main.lib.shared_models.shared_model import SharedModel
from app.main import db
from app.main.model.context_hash import ContextHash

task = {"url": "http://devingaffney.com/files/sample-videos/sample-videos/pattern-sd-with-large-logo-bar.mp4", "id": 12343}
class VideoModel(SharedModel):
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
        context_hash = ContextHash.from_context(task.get("context", {}))
        filepath = self.tmk_file_path(task, context_hash)
        if os.path.exists(filepath):
            os.remove(filepath)
        return {"requested": task, "result": {"outfile": filepath}}

    def add(self, task):
        context_hash = ContextHash.from_context(task.get("context", {}))
        temp_video_file = self.get_tempfile()
        remote_request = urllib.request.Request(task["url"], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(remote_request) as response, open(temp_video_file.name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        outfile = self.tmk_file_path(task, context_hash)
        hash_video_command = self.tmk_hash_video_command()
        result = self.execute_command(f"{hash_video_command} -f {self.ffmpeg_dir} -i {temp_video_file.name} -o {outfile}")
        return {"requested": task, "result": {"outfile": outfile}}

    def search(self, task):
        context_hash = ContextHash.from_context(task.get("context", {}))
        temp_search_file = self.get_tempfile()
        temp_comparison_file = self.get_tempfile()
        with open(temp_search_file.name, 'w') as out_file:
            out_file.write(str.join("\n", self.get_fullpath_files(context_hash)))
        with open(temp_comparison_file.name, 'w') as out_file:
            out_file.write(self.tmk_file_path(task, context_hash))
        tmk_query_command = self.tmk_query_command()
        result = self.execute_command(f"{tmk_query_command} --c1 -1.0 --c2 0.0 {temp_search_file.name} {temp_comparison_file.name}")
        return self.parse_search_results(result, context_hash)

    def tmk_dir(self):
        return "./threatexchange/tmk/cpp/"

    def tmk_query_command(self):
        return f"{self.tmk_dir()}tmk-query"

    def tmk_hash_video_command(self):
        return f"{self.tmk_dir()}tmk-hash-video"

    def tmk_directory(self, context_hash):
        return f"{self.directory}/{context_hash.hash_key}"

    def tmk_file_path(self, task, context_hash):
        if context_hash.context.get("has_custom_id"):
            task_id = "custom_"+task.get("doc_id")
        else:
            task_id = "id_"+task.get("project_media_id")
        pathlib.Path(f"{self.directory}/{context_hash.hash_key}").mkdir(parents=True, exist_ok=True)
        return f"{self.directory}/{context_hash.hash_key}/{task_id}.tmk"
        
    def get_fullpath_files(self, context_hash):
        directory = self.tmk_directory(context_hash)
        full_paths = []
        for path in os.listdir(directory):
            full_path = os.path.join(directory, path)
            if os.path.isfile(full_path):
                full_paths.append(full_path)
        return full_paths

    def media_id_from_filepath(self, filepath):
        if filepath[0:3] == "id_":
            return os.path.basename(filepath).replace(".tmk", "")
        elif filepath[0:7] == "custom_":
            return base64.standard_b64decode(filepath.replace(".tmk", "==").replace("custom_", "")).split("-")[2]

    def parse_search_results(self, result, context_hash):
        results = []
        for row in result.split("\n")[:-1]:
            level1, level2, first_file, second_file = row.split(" ")
            context = context_hash.context
            context["project_media_id"] = self.media_id_from_filepath(first_file)
            results.append({
                "hash_key": context_hash.hash_key,
                "context": context,
                "score": level2,
                "filename": first_file,
            })
        return results