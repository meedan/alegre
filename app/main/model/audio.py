import urllib.request
import tempfile
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, BIT, ARRAY
from scipy.io import wavfile
import scipy.signal
import numpy as np
from pydub import AudioSegment #requires ffmpeg and ffprobe to be on the PATH
import timeout_decorator

from app.main import db

# @timeout_decorator.timeout(15)
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

  @staticmethod
  def from_url(url, doc_id, context={}, hash_value=[]):
    """Fetch an audio from a URL and load it
      :param url: Audio URL
      :param doc_id: Audio Doc ID
      :param context: Audio Context
      :param hash_value: Audio fingerprint
      :returns: Audio object
    """
    return Audio(chromaprint_fingerprint=hash_value, doc_id=doc_id, url=url, context=context)