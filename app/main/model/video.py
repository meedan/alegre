import uuid
from sqlalchemy.dialects.postgresql import JSONB

from app.main import db

class Video(db.Model):
  """ Model for storing video related details """
  __tablename__ = 'videos'

  id = db.Column(db.Integer, primary_key=True)
  doc_id = db.Column(db.String(255, convert_unicode=True), nullable=True, index=True, unique=True)
  folder = db.Column(db.String(255, convert_unicode=True), nullable=False, index=False)
  filepath = db.Column(db.String(255, convert_unicode=True), nullable=False, index=False)
  url = db.Column(db.String(255, convert_unicode=True), nullable=False, index=True)
  context = db.Column(JSONB(), default=[], nullable=False)
  __table_args__ = (
    db.Index('ix_videos_context', context, postgresql_using='gin'),
  )

  def __init__(self, doc_id, url, context):
    self.doc_id = doc_id
    self.filepath = str(uuid.uuid4())
    self.folder = self.filepath.split("-")[1]
    self.url = url
    self.context = context