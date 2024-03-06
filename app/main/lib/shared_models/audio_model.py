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
from app.main.lib import media_crud
from app.main import db
from app.main.model.audio import Audio
from app.main.lib.presto import Presto

def _after_log(retry_state):
  app.logger.debug("Retrying audio similarity...")

class AudioModel(SharedModel):
    def delete(self, task):
        return media_crud.delete(task, Audio)

    def add(self, task):
        return media_crud.add(task, Audio, ["hash_value", "chromaprint_fingerprint"])

    def blocking_search(self, task, modality):
        audio, temporary, context, presto_result = media_crud.get_blocked_presto_response(task, Audio, modality)
        audio.chromaprint_fingerprint = presto_result["body"]["result"]["hash_value"]
        if audio:
            matches = self.search_by_hash_value(audio.chromaprint_fingerprint, task.get("threshold", 0.0), context[0])
            if temporary:
                media_crud.delete(task, Audio)
            else:
                media_crud.save(audio, Audio, ["hash_value", "chromaprint_fingerprint"])
            if task.get("limit"):
                return {"result": matches[:task.get("limit")]}
            else:
                return {"result": matches}
        else:
            return {"error": "Audio not found for provided task", "task": task}

    def async_search(self, task, modality):
        return media_crud.get_async_presto_response(task, Audio, modality)

    def search(self, task):
        # here, we have to unpack the task contents to pull out the body,
        # which may be embedded in a body key in the dict if its coming from a presto callback.
        # alternatively, the "body" is just the entire dictionary.
        if "body" in task:
            body = task.get("body", {})
            threshold = task.get("raw", {}).get('threshold', 0.0)
            limit = body.get("raw", {}).get("limit")
            if not body.get("raw"):
                body["raw"] = {}
            body["hash_value"] = task.get("body", {}).get("hash_value")
        else:
            body = task
            threshold = body.get('threshold', 0.0)
            limit = body.get("limit")
        audio, temporary = media_crud.get_object(body, Audio)
        if audio.chromaprint_fingerprint is None:
            callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], "audio")
            if task.get("doc_id") is    None:
                task["doc_id"] = str(uuid.uuid4())
            response = json.loads(Presto.send_request(app.config['PRESTO_HOST'], "audio__Model", callback_url, task, False).text)
            # Warning: this is a blocking hold to wait until we get a response in 
            # a redis key that we've received something from presto.
            result = Presto.blocked_response(response, "audio")
            audio.chromaprint_fingerprint = result["body"]["result"]["hash_value"]
        if audio:
            matches = self.search_by_hash_value(audio.chromaprint_fingerprint, threshold, body["context"])
            if temporary:
                media_crud.delete(body, Audio)
            if limit:
                return {"result": matches[:limit]}
            else:
                return {"result": matches}
        else:
            return {"error": "Audio not found for provided task", "task": task}

    def respond(self, task):
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
            context_query, context_hash = get_context_query(context)
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
