import os
import io
import urllib.request
import logging
import sys
from flask import current_app as app
from PIL import Image, ImageFile
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import BIT, JSONB

from app.main import db
from app.main.lib.image_hash import sha256_stream
from app.main.lib import media_crud
from pgvector.sqlalchemy import Vector

logging.basicConfig(level=logging.INFO)

class ImageModel(db.Model):
  """ Model for storing image related details """
  __tablename__ = 'images'

  id = db.Column(db.Integer, primary_key=True)
  sha256 = db.Column(db.String(255, convert_unicode=True), nullable=True, index=True)
  doc_id = db.Column(db.String(255, convert_unicode=True), nullable=True, index=True, unique=True)
  phash = db.Column(db.BigInteger, nullable=True, index=True)
  pdq = db.Column(BIT(256), nullable=True, index=True)
  sscd = db.Column(Vector(512), nullable=True)
  url = db.Column(db.String(255, convert_unicode=True), nullable=False, index=True)
  context = db.Column(JSONB(), default=[], nullable=False)
  created_at = db.Column(db.DateTime, nullable=True)
  __table_args__ = (
    db.Index('ix_images_context_gin', context, postgresql_using='gin'),
    db.Index('ix_images_team_id_partial', text("(context->>'team_id')"), postgresql_where=text("context->>'team_id' IS NOT NULL")),
    db.Index('ix_images_has_custom_id_partial', text("(context->>'has_custom_id')"), postgresql_where=text("context->>'has_custom_id' IS NOT NULL")),
  )

  @property
  def existing_response(self):
    model = app.config['IMAGE_MODEL']
    if model == "pdq":
      return {"body": {"hash_value": self.pdq}}
    return {"body": {"hash_value": self.phash}}

  @property
  def requires_encoding(self):
    model = app.config['IMAGE_MODEL']
    return model and ((model.lower() == "pdq" and not self.pdq) or (model.lower() == "phash" and not self.phash))

  @classmethod
  def from_task_data(cls, task, existing):
    if existing:
      if os.getenv("IMAGE_MODEL") == 'pdq':
          if not existing.pdq:
            existing.pdq = task.get("hash_value")
      elif os.getenv("IMAGE_MODEL") == 'phash':
          if not existing.phash:
            existing.phash = task.get("hash_value")
      return media_crud.ensure_context_appended(task, existing)
    return cls(
      pdq=task.get("hash_value"),
      doc_id=task.get("doc_id", task.get("raw", {}).get("doc_id")),
      url=task.get("url"),
      context=task.get("context", task.get("raw", {}).get("context"))
    )

  @staticmethod
  def from_url(url, doc_id, context={}, created_at=None):
    """Fetch an image from a URL and load it
      :param url: Image URL
      :returns: ImageModel object
    """
    app.logger.info(f"Starting image hash for doc_id {doc_id}.")
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    remote_request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    remote_response = urllib.request.urlopen(remote_request)
    raw = remote_response.read()
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    sha256 = sha256_stream(io.BytesIO(raw))
    return ImageModel(sha256=sha256, phash=None, pdq=None, url=url, context=context, doc_id=doc_id, created_at=created_at, sscd=None)
