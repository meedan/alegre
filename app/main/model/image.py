import io
import urllib.request
from PIL import Image
from sqlalchemy.dialects.postgresql import JSONB

from app.main import db
from app.main.lib.image_hash import compute_phash_int, sha256_stream

class ImageModel(db.Model):
  """ Model for storing image related details """
  __tablename__ = 'images'

  id = db.Column(db.Integer, primary_key=True)
  sha256 = db.Column(db.String(64, convert_unicode=True), nullable=False, index=True)
  phash = db.Column(db.BigInteger, nullable=False, index=True)
  url = db.Column(db.String(255, convert_unicode=True), nullable=False, index=True)
  context = db.Column(JSONB(), default={}, nullable=False)
  __table_args__ = (
    db.Index('ix_images_context', context, postgresql_using='gin'),
  )

  @staticmethod
  def from_url(url, context={}):
    """Fetch an image from a URL and load it
      :param url: Image URL
      :returns: ImageModel object
    """
    remote_request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    remote_response = urllib.request.urlopen(remote_request)
    raw = remote_response.read()
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    phash = compute_phash_int(im)
    sha256 = sha256_stream(io.BytesIO(raw))
    return ImageModel(sha256=sha256, phash=phash, url=url, context=context)
