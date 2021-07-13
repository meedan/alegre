import binascii
import uuid
import os
import tempfile
import pathlib
import urllib.error
import urllib.request
import shutil
from flask import current_app as app
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import text
import tenacity
from sqlalchemy.orm.exc import NoResultFound

from app.main.lib.shared_models.shared_model import SharedModel
from app.main import db
from app.main.model.audio import Audio

def _after_log(retry_state):
  app.logger.debug("Retrying audio similarity...")

def parse_db_hash_value(hash_value):
    return binascii.b2a_hex(hash_value).decode("utf-8")[1::2]

class AudioModel(SharedModel):
    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def save(self, audio):
        saved_audio = None
        try:
            # First locate existing audio and append new context
            existing = db.session.query(Audio).filter(Audio.url==audio.url).one()
            if audio.context not in existing.context:
                existing.context.append(audio.context)
                flag_modified(existing, 'context')
            saved_audio = existing
        except NoResultFound as e:
            # Otherwise, add new audio, but with context as an array
            if audio.context and not isinstance(audio.context, list):
                audio.context = [audio.context]
            db.session.add(audio)
            saved_audio = audio
        except Exception as e:
            db.session.rollback()
            raise e
        try:
            db.session.commit()
            return saved_audio
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
            audios = db.session.query(Audio).filter(Audio.doc_id==task.get("doc_id")).all()
            if audios:
                audio = audios[0]
        elif 'url' in task:
            audios = db.session.query(Audio).filter(Audio.url==task.get("url")).all()
            if audios:
                audio = audios[0]
        deleted = db.session.query(Audio).filter(Audio.id==audio.id).delete()
        return {"requested": task, "result": {"url": audio.url, "deleted": deleted}}

    def add(self, task):
        try:
            audio = Audio.from_url(task.get("url"), task.get("doc_id"), task.get("context", {}))
            audio = self.save(audio)
            return {"requested": task, "result": {"url": audio.url}, "success": True}
        except urllib.error.HTTPError:
            return {"requested": task, "result": {"url": audio.url}, "success": False}

    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def search_by_context(self, context):
        try:
            context_query, context_hash = self.get_context_query(context)
            if context_query:
                cmd = """
                  SELECT id, doc_id, url, hash_value, context FROM audios
                  WHERE 
                """+context_query
            else:
                cmd = """
                  SELECT id, doc_id, url, hash_value, context FROM audios
                """
            matches = db.session.execute(text(cmd), context_hash).fetchall()
            keys = ('id', 'doc_id', 'url', 'hash_value', 'context')
            return [dict(zip(keys, values)) for values in matches]
        except Exception as e:
            db.session.rollback()
            raise e

    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def search_by_hash_value(self, hash_value, threshold, context):
        try:
            context_query, context_hash = self.get_context_query(context)
            if context_query:
                cmd = """
                  SELECT * FROM (
                    SELECT id, doc_id, hash_value, url, context, bit_count_audio(hash_value # :hash_value)
                    AS score FROM audios
                  ) f
                  WHERE score <= :threshold
                  AND 
                  """+context_query+"""
                  ORDER BY score ASC
                """
            else:
                cmd = """
                  SELECT * FROM (
                    SELECT id, doc_id, hash_value, phash, url, context, bit_count_audio(hash_value # :hash_value)
                    AS score FROM audios
                  ) f
                  WHERE score <= :threshold
                  ORDER BY score ASC
                """
            matches = db.session.execute(text(cmd), dict(**{
                'hash_value': hash_value,
                'threshold': threshold,
            }, **context_hash)).fetchall()
            keys = ('id', 'doc_id', 'hash_value', 'url', 'context', 'score')
            rows = []
            for values in matches:
                row = dict(zip(keys, values))
                row["score"] = 1-(row["score"]/float(Audio.hash_value.type.length))
                rows.append(row)
            return rows
        except Exception as e:
            db.session.rollback()
            raise e

    def search(self, task):
        context = {}
        audio = None
        if task.get('context'):
            context = task.get('context')
        elif task.get('url'):
            audios = db.session.query(Audio).filter(Audio.url==task.get("url")).all()
            if audios and not audio:
                audio = audios[0]
        if task.get('doc_id'):
            audios = db.session.query(Audio).filter(Audio.doc_id==task.get("doc_id")).all()
            if audios and not audio:
                audio = audios[0]
        elif task.get('url'):
            audios = db.session.query(Audio).filter(Audio.url==task.get("url")).all()
            if audios and not audio:
                audio = audios[0]
        if audio:
            threshold = round((1-(task.get('threshold', 0.0) or 0.0))*Audio.hash_value.type.length)
            matches = self.search_by_hash_value(audio.hash_value, threshold, context)
            return {"result": matches}
        else:
            return {"error": "Audio not found for provided task", "task": task}

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
    