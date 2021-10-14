import urllib.request
import tempfile
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, BIT, ARRAY
from scipy.io import wavfile
import scipy.signal
import numpy as np
from pydub import AudioSegment #requires ffmpeg and ffprobe to be on the PATH
import timeout_decorator
import acoustid

from app.main import db

# @timeout_decorator.timeout(15)
def audio_hasher(filename):
  return acoustid.chromaprint.decode_fingerprint(
    acoustid.fingerprint_file(filename)[1]
  )[0]

class Audio(db.Model):
  """ Model for storing video related details """
  __tablename__ = 'audios'

  id = db.Column(db.Integer, primary_key=True)
  doc_id = db.Column(db.String(255, convert_unicode=True), nullable=True, index=True, unique=True)
  url = db.Column(db.String(255, convert_unicode=True), nullable=False, index=True)
  hash_value = db.Column(BIT(length=128), nullable=True, index=True)
  chromaprint_fingerprint = db.Column(ARRAY(db.Integer), nullable=True)
  context = db.Column(JSONB(), default=[], nullable=False)
  __table_args__ = (
    db.Index('ix_audios_context', context, postgresql_using='gin'),
  )

  def __init__(self, chromaprint_fingerprint, doc_id, url, context):
    self.doc_id = doc_id
    self.chromaprint_fingerprint = chromaprint_fingerprint
    self.url = url
    self.context = context


  @staticmethod
  def from_url(url, doc_id, context={}):
    """Fetch an audio from a URL and load it
      :param url: Audio URL
      :returns: Audio object
    """
    remote_request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    remote_response = urllib.request.urlopen(remote_request)
    temp_file = tempfile.NamedTemporaryFile()
    with open(temp_file.name, 'wb') as out_file:
      out_file.write(remote_response.read())
    return Audio(audio_hasher(temp_file.name), doc_id, url, context)
