from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.main import db

class Node(db.Model):
  """ Model for storing node """
  __tablename__ = 'nodes'

  id = db.Column(db.Integer, primary_key=True)
  node_data_type = db.Column(db.String(500, convert_unicode=True), nullable=False)
  node_data_type_id = db.Column(db.Integer, nullable=False, index=True)
  node_context = db.Column(JSONB(), default=[], nullable=False)
  node_data = db.Column(JSONB(), default=[], nullable=False)

  __table_args__ = (
      db.Index('node_id_constraint', node_data_type, node_data_type_id, unique=True),
  )