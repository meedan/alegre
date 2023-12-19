import uuid
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from app.main import db


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
  __table_args__ = (
    db.Index('ix_videos_context', context, postgresql_using='gin'),
  )

  def __init__(self, **kwargs):
    self.filepath = str(uuid.uuid4())
    self.folder = self.filepath.split("-")[1]
    super().__init__(**kwargs)

  @classmethod
  def from_task_data(cls, task):
    temp_uuid = str(uuid.uuid4())
    return cls(
      hash_value=task.get("hash_value"),
      folder=task.get("folder", temp_uuid.split("-")[1]),
      filepath=task.get("filepath", temp_uuid),
      doc_id=task.get("doc_id", task.get("raw", {}).get("doc_id")),
      url=task.get("url"),
      context=task.get("context", task.get("raw", {}).get("context"))
    )