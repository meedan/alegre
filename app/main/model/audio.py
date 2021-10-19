import urllib.request
import tempfile
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, BIT
from scipy.io import wavfile
import scipy.signal
import numpy as np
from pydub import AudioSegment #requires ffmpeg and ffprobe to be on the PATH
import timeout_decorator

from app.main import db

# @timeout_decorator.timeout(15)
def audio_hasher(sound,hash_size=128,average=np.median):
  #if len(audio)<hash_size raise Exception. This should never really happen.
  channel_sounds = sound.split_to_mono()
  samples = [s.get_array_of_samples() for s in channel_sounds]
  fp_arr = np.array(samples).T.astype(np.float32)
  fp_arr /= np.iinfo(samples[0].typecode).max
  audio=fp_arr
  sampling_rate=round(len(fp_arr)/(len(sound)/1000))
  if len(audio.shape)==2:
    if audio.shape[1]==2:
      audio = (audio[:,0]+audio[:,1])/2.0
    else:
      audio=audio[:,0]
  resampled=scipy.signal.resample(audio,hash_size)
  med=average(resampled)
  return str.join("", [str(int(b)) for b in (resampled>med).flatten().tolist()])

class Audio(db.Model):
  """ Model for storing video related details """
  __tablename__ = 'audios'

  id = db.Column(db.Integer, primary_key=True)
  doc_id = db.Column(db.String(255, convert_unicode=True), nullable=True, index=True, unique=True)
  url = db.Column(db.String(255, convert_unicode=True), nullable=False, index=True)
  hash_value = db.Column(BIT(length=128), nullable=False, index=True)
  context = db.Column(JSONB(), default=[], nullable=False)
  __table_args__ = (
    db.Index('ix_audios_context', context, postgresql_using='gin'),
  )

  def __init__(self, hash_value, doc_id, url, context):
    self.doc_id = doc_id
    self.hash_value = hash_value
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
    if ".aac" in url:
      sound = AudioSegment.from_file(temp_file, "aac")
    else:
      sound = AudioSegment.from_file(temp_file)
    # sound = sound.set_channels(1)
    return Audio(audio_hasher(sound), doc_id, url, context)
