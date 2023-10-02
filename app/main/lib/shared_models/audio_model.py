import json
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
import sqlalchemy
import tenacity
import numpy as np
from sqlalchemy.orm.exc import NoResultFound

from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.helpers import context_matches
from app.main.lib.similarity_helpers import get_context_query, drop_context_from_record
from app.main import db
from app.main.model.audio import Audio
from app.main.lib.presto import Presto

def _after_log(retry_state):
  app.logger.debug("Retrying audio similarity...")

class AudioModel(SharedModel):
    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def save(self, audio):
        saved_audio = None
        try:
            # First locate existing audio and append new context
            existing = db.session.query(Audio).filter(Audio.url==audio.url).one()
            if existing:
                if audio.hash_value is not None  and not existing.hash_value:
                    existing.hash_value = audio.hash_value
                    flag_modified(existing, 'hash_value')
                if audio.chromaprint_fingerprint is not None and not existing.chromaprint_fingerprint:
                    existing.chromaprint_fingerprint = audio.chromaprint_fingerprint
                    flag_modified(existing, 'chromaprint_fingerprint')
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
        return saved_audio

    def respond(self, task):
        if task["command"] == "delete":
            return self.delete(task)
        elif task["command"] == "add":
            return self.add(task)
        elif task["command"] == "search":
            return self.search(task)

    def delete(self, task):
        deleted = False
        audio = None
        if 'doc_id' in task:
            audios = db.session.query(Audio).filter(Audio.doc_id==task.get("doc_id")).all()
            if audios:
                audio = audios[0]
        elif 'url' in task:
            audios = db.session.query(Audio).filter(Audio.url==task.get("url")).all()
            if audios:
                audio = audios[0]
        if audio:
            if task.get("context", {}) in audio.context and len(audio.context) > 1:
                deleted = drop_context_from_record(audio, task.get("context", {}))
            else:
                deleted = db.session.query(Audio).filter(Audio.id==audio.id).delete()
            return {"requested": task, "result": {"url": audio.url, "deleted": deleted}}
        else:
            return {"requested": task, "result": {"url": task.get("url"), "deleted": False}}

    def add(self, task):
        try:
            body = task.get("body", {})
            audio = Audio.from_url(body.get("url"), body.get("raw", {}).get("doc_id"), body.get("raw", {}).get("context", {}), task.get("response", {}).get("hash_value"))
            try:
              audio = self.save(audio)
            except sqlalchemy.exc.IntegrityError:
              audio = None
            if audio:
              return {"requested": task, "result": {"url": audio.url}, "success": True}
            else:
              return {"requested": task, "result": {"url": task.get("url")}, "success": False}
        except urllib.error.HTTPError:
            return {"requested": task, "result": {"url": task.get("url")}, "success": False}

    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def search_by_context(self, context):
        try:
            context_query, context_hash = get_context_query(context, True)
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
            rows = [dict(zip(keys, values)) for values in matches]
            for row in rows:
                row["context"] = [c for c in row["context"] if context_matches(context, c)]
                row["model"] = "audio"
            return rows
        except Exception as e:
            db.session.rollback()
            raise e

    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def search_by_hash_value(self, chromaprint_fingerprint, threshold, context):
        try:
            context_query, context_hash = get_context_query(context, True)
            if context_query:
                cmd = """
                  SELECT audio_similarity_functions();
                  SELECT * FROM (
                    SELECT id, doc_id, chromaprint_fingerprint, url, context, get_audio_chromaprint_score(chromaprint_fingerprint, :chromaprint_fingerprint)
                    AS score FROM audios
                  ) f
                  WHERE score >= :threshold
                  AND 
                  """+context_query+"""
                  ORDER BY score DESC
                """
            else:
                cmd = """
                  SELECT audio_similarity_functions();
                  SELECT * FROM (
                    SELECT id, doc_id, chromaprint_fingerprint, url, context, get_audio_chromaprint_score(chromaprint_fingerprint, :chromaprint_fingerprint)
                    AS score FROM audios
                  ) f
                  WHERE score >= :threshold
                  ORDER BY score DESC
                """
            matches = db.session.execute(text(cmd), dict(**{
                'chromaprint_fingerprint': chromaprint_fingerprint,
                'threshold': threshold,
            }, **context_hash)).fetchall()
            keys = ('id', 'doc_id', 'chromaprint_fingerprint', 'url', 'context', 'score')
            rows = []
            for values in matches:
                row = dict(zip(keys, values))
                row["model"] = "audio"
                row["score"] = row["score"]
                rows.append(row)
            return rows
        except Exception as e:
            db.session.rollback()
            raise e

    def get_by_doc_id_or_url(self, task):
        audio = None
        if task.get('doc_id'):
            audios = db.session.query(Audio).filter(Audio.doc_id==task.get("doc_id")).all()
            if audios and not audio:
                audio = audios[0]
        elif task.get('url'):
            audios = db.session.query(Audio).filter(Audio.url==task.get("url")).all()
            if audios and not audio:
                audio = audios[0]
        return audio

    def get_audio(self, task):
        temporary = False
        audio = self.get_by_doc_id_or_url(task)
        if audio is None:
            temporary = True
            if not task.get("raw"):
                task["raw"] = {"doc_id": str(uuid.uuid4())}
            self.add(dict(**{"body": task}, **task))
            audios = db.session.query(Audio).filter(Audio.doc_id==task["raw"].get("doc_id")).all()
            if audios and not audio:
                audio = audios[0]
        return audio, temporary

    def get_context_for_search(self, task):
        context = {}
        if task.get('context'):
            context = task.get('context')
        if task.get("match_across_content_types"):
            context.pop("content_type", None)
        return context

    def search(self, task):
        # here, we have to unpack the task contents to pull out the body,
        # which may be embedded in a body key in the dict if its coming from a presto callback.
        # alternatively, the "body" is just the entire dictionary.
        if "body" in task:
            body = task.get("body", {})
            threshold = task.get("raw", {}).get('threshold', 0.0)
            limit = body.get("raw", {}).get("limit")
        else:
            body = task
            threshold = body.get('threshold', 0.0)
            limit = body.get("limit")
        audio, temporary = self.get_audio(body)
        context = self.get_context_for_search(body)
        if audio.chromaprint_fingerprint is None:
            callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], "audio")
            if task.get("doc_id") is None:
                task["doc_id"] = str(uuid.uuid4())
            response = json.loads(Presto.send_request(app.config['PRESTO_HOST'], "audio__Model", callback_url, task).text)
            # Warning: this is a blocking hold to wait until we get a response in 
            # a redis key that we've received something from presto.
            result = Presto.blocked_response(response, "audio")
            audio.chromaprint_fingerprint = result["response"]["hash_value"]
            context = self.get_context_for_search(result["body"]["raw"])
        if audio:
            matches = self.search_by_hash_value(audio.chromaprint_fingerprint, threshold, context)
            if temporary:
                self.delete(body)
            if limit:
                return {"result": matches[:limit]}
            else:
                return {"result": matches}
        else:
            return {"error": "Audio not found for provided task", "task": task}
    
