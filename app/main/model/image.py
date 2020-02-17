from .. import db, flask_bcrypt

from sqlalchemy.dialects.postgresql import JSONB

class Image(db.Model):
  """ Image Model for storing image related details """
  __tablename__ = 'images'

  id = db.Column(db.Integer, primary_key=True)
  sha256 = db.Column(db.String(64, convert_unicode=True), nullable=False, unique=True)
  phash = db.Column(db.BigInteger, nullable=False, index=True)
  ext = db.Column(db.String(4, convert_unicode=True), nullable=False)
  url = db.Column(db.String(255, convert_unicode=True), nullable=False)
  context = db.Column(JSONB(), default={}, nullable=False)
  __table_args__ = (
    db.Index('ix_images_context', context, postgresql_using='gin'),
  )
