import urllib.request
import tempfile
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, BIT, ARRAY
from scipy.io import wavfile
import scipy.signal
import numpy as np
from flask import current_app as app
from app.main.lib import media_crud
from app.main import db

class Audio(db.Model):
  """ Model for storing video related details """
  __tablename__ = 'audios'

  id = db.Column(db.Integer, primary_key=True)
  doc_id = db.Column(db.String(255), nullable=True, index=True, unique=True)
  url = db.Column(db.String(255), nullable=False, index=True)
  hash_value = db.Column(BIT(length=128), nullable=True, index=True)
  chromaprint_fingerprint = db.Column(ARRAY(db.Integer), nullable=True)
  context = db.Column(JSONB(), default=[], nullable=False)
  created_at = db.Column(db.DateTime, nullable=True)
  __table_args__ = (
    db.Index('ix_audios_context', context, postgresql_using='gin'),
  )

  @property
  def existing_response(self):
    return {"body": {"hash_value": self.chromaprint_fingerprint}}

  @property
  def requires_encoding(self):
    if self.chromaprint_fingerprint:
      return False
    return True

  @classmethod
  def from_task_data(cls, task, existing):
    if existing:
      if not existing.chromaprint_fingerprint:
        existing.chromaprint_fingerprint = task.get("hash_value")
      return media_crud.ensure_context_appended(task, existing)
    return cls(
      chromaprint_fingerprint=task.get("hash_value"),
      doc_id=task.get("doc_id", task.get("raw", {}).get("doc_id")),
      url=task.get("url"),
      context=task.get("context", task.get("raw", {}).get("context"))
    )
