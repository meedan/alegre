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
import tenacity
import numpy as np
from sqlalchemy.orm.exc import NoResultFound

from app.main.lib.shared_models.shared_model import SharedModel
from app.main import db
from app.main.model.audio import Audio

def _after_log(retry_state):
  app.logger.debug("Retrying audio similarity...")

def parse_db_hash_value(hash_value):
    return binascii.b2a_hex(hash_value).decode("utf-8")[1::2]

def correlation(listx, listy):
    if len(listx) == 0 or len(listy) == 0:
        # Error checking in main program should prevent us from ever being
        # able to get here.
        raise Exception('Empty lists cannot be correlated.')
    if len(listx) > len(listy):
        listx = listx[:len(listy)]
    elif len(listx) < len(listy):
        listy = listy[:len(listx)]
    covariance = 0
    for i in range(len(listx)):
        covariance += 32 - bin(listx[i] ^ listy[i]).count("1")
    covariance = covariance / float(len(listx))
    return covariance/32
  
# return cross correlation, with listy offset from listx
def cross_correlation(listx, listy, offset, min_overlap=20):
    if offset > 0:
        listx = listx[offset:]
        listy = listy[:len(listx)]
    elif offset < 0:
        offset = -offset
        listy = listy[offset:]
        listx = listx[:len(listy)]
    if min(len(listx), len(listy)) < min_overlap:
        # Error checking in main program should prevent us from ever being
        # able to get here.
        return 
    #raise Exception('Overlap too small: %i' % min(len(listx), len(listy)))
    return correlation(listx, listy)
  
# cross correlate listx and listy with offsets from -span to span
def compare(listx, listy, span, step):
    if span > min(len(listx), len(listy)):
        span = min(len(listx), len(listy)) -1
    corr_xy = []
    for offset in np.arange(-span, span + 1, step):
        corr_xy.append(cross_correlation(listx, listy, offset))
    return corr_xy
  
# return index of maximum value in list
def max_index(listx):
    max_index = 0
    max_value = listx[0]
    for i, value in enumerate(listx):
        if value and max_value and value > max_value:
            max_value = value
            max_index = i
    return max_index
  
def get_max_corr(corr, source, target, threshold, span, step):
    max_corr_index = max_index(corr)
    max_corr_offset = -span + max_corr_index * step
    return corr[max_corr_index]

def get_score(first, second, threshold, span=150, step=1):
    corr = compare(first, second, span, step)
    return get_max_corr(corr, first, second, threshold, span, step)

class AudioModel(SharedModel):
    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def save(self, audio):
        saved_audio = None
        try:
            # First locate existing audio and append new context
            existing = db.session.query(Audio).filter(Audio.url==audio.url).one()
            if existing:
                if audio.hash_value and not existing.hash_value:
                    existing.hash_value = audio.hash_value
                    flag_modified(existing, 'hash_value')
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
            rows = [dict(zip(keys, values)) for values in matches]
            for row in rows:
                row["context"] = [c for c in row["context"] if self.context_matches(context, c)]
            return rows
        except Exception as e:
            db.session.rollback()
            raise e

    def context_matches(self, context, search_context):
        for k,v in context.items():
            if search_context.get(k) != v:
                return False
        return True

    @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
    def search_by_hash_value(self, chromaprint_fingerprint, threshold, context):
        try:
            context_query, context_hash = self.get_context_query(context)
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
                # row["score"] = get_score(row["chromaprint_fingerprint"], chromaprint_fingerprint, threshold)
                rows.append(row)
            return rows
        except Exception as e:
            db.session.rollback()
            raise e

    def search(self, task):
        context = {}
        audio = None
        temporary = False
        if task.get('context'):
            context = task.get('context')
        if task.get("match_across_content_types"):
            context.pop("content_type", None)
        if task.get('doc_id'):
            audios = db.session.query(Audio).filter(Audio.doc_id==task.get("doc_id")).all()
            if audios and not audio:
                audio = audios[0]
        elif task.get('url'):
            audios = db.session.query(Audio).filter(Audio.url==task.get("url")).all()
            if audios and not audio:
                audio = audios[0]
        if audio is None:
            temporary = True
            if not task.get("doc_id"):
                task["doc_id"] = str(uuid.uuid4())
            self.add(task)
            audios = db.session.query(Audio).filter(Audio.doc_id==task.get("doc_id")).all()
            if audios and not audio:
                audio = audios[0]
        if audio:
            threshold = round((1-(task.get('threshold', 0.0) or 0.0))*Audio.hash_value.type.length)
            matches = self.search_by_hash_value(audio.chromaprint_fingerprint, threshold, context)
            if temporary:
                self.delete(task)
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
                        context_clause += "context @> '[{\""+key+"\": "+json.dumps(value)+"}]'"
                        if len(value)-1 != i:
                            context_clause += " OR "
                        context_hash[f"context_{key}_{i}"] = v
                    context_clause += ")"
                    context_query.append(context_clause)
                else:
                    context_query.append("context @>'[{\""+key+"\": "+json.dumps(value)+"}]'")
                    context_hash[f"context_{key}"] = value
        return str.join(" AND ",  context_query), context_hash
    