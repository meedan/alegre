import os
import uuid
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from app.main import db
from app.main.lib import media_crud

class Video(db.Model):
  """ Model for storing video related details """
  __tablename__ = 'videos'

  id = db.Column(db.Integer, primary_key=True)
  doc_id = db.Column(db.String(255, convert_unicode=True), nullable=True, index=True, unique=True)
  folder = db.Column(db.String(255, convert_unicode=True), nullable=False, index=False)
  filepath = db.Column(db.String(255, convert_unicode=True), nullable=False, index=False)
  url = db.Column(db.String(255, convert_unicode=True), nullable=False, index=True)
  hash_value = db.Column(ARRAY(db.Float), nullable=True)
  context = db.Column(JSONB(), default=[], nullable=False)
  created_at = db.Column(db.DateTime, nullable=True)
  tmk_file_downloaded = db.Column(db.Boolean, nullable=True)
  __table_args__ = (
    db.Index('ix_videos_context_gin', context, postgresql_using='gin'),
    db.Index('ix_videos_team_id_partial', text("(context->>'team_id')"), postgresql_where=text("context->>'team_id' IS NOT NULL")),
    db.Index('ix_videos_has_custom_id_partial', text("(context->>'has_custom_id')"), postgresql_where=text("context->>'has_custom_id' IS NOT NULL")),
  )

  def __init__(self, **kwargs):
    self.filepath = str(uuid.uuid4())
    self.folder = self.filepath.split("-")[1]
    super().__init__(**kwargs)

  @property
  def existing_response(self):
    return {
      "body": {
        "hash_value": self.hash_value,
        "folder": self.folder,
        "filepath": self.filepath
      }
    }

  @property
  def fingerprint_file_exists(self):
    return os.path.exists(
      media_crud.tmk_file_path(
      self.folder,
      self.filepath,
      False
      )
    )

  @property
  def requires_encoding(self):
    return not (self.hash_value and self.fingerprint_file_exists)

  @classmethod
  def from_task_data(cls, task, existing):
    if existing:
      if not existing.hash_value:
        existing.hash_value = task.get("hash_value")
      return media_crud.ensure_context_appended(task, existing)
    temp_uuid = str(uuid.uuid4())
    return cls(
      hash_value=task.get("hash_value"),
      folder=task.get("folder", temp_uuid.split("-")[1]),
      filepath=task.get("filepath", temp_uuid),
      doc_id=task.get("doc_id", task.get("raw", {}).get("doc_id")),
      url=task.get("url"),
      context=task.get("context", task.get("raw", {}).get("context")),
      tmk_file_downloaded=False,
    )
