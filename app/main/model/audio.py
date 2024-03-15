import urllib.request
import tempfile
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, BIT, ARRAY
from scipy.io import wavfile
import scipy.signal
import numpy as np

from app.main import db

class Audio(db.Model):
  """ Model for storing video related details """
  __tablename__ = 'audios'

  id = db.Column(db.Integer, primary_key=True)
  doc_id = db.Column(db.String(255, convert_unicode=True), nullable=True, index=True, unique=True)
  url = db.Column(db.String(255, convert_unicode=True), nullable=False, index=True)
  hash_value = db.Column(BIT(length=128), nullable=True, index=True)
  chromaprint_fingerprint = db.Column(ARRAY(db.Integer), nullable=True)
  context = db.Column(JSONB(), default=[], nullable=False)
  created_at = db.Column(db.DateTime, nullable=True)
  __table_args__ = (
    db.Index('ix_audios_context', context, postgresql_using='gin'),
  )

  @classmethod
  def from_task_data(cls, task):
    return cls(
      chromaprint_fingerprint=task.get("hash_value"),
      doc_id=task.get("doc_id", task.get("raw", {}).get("doc_id")),
      url=task.get("url"),
      context=task.get("context", task.get("raw", {}).get("context"))
    )