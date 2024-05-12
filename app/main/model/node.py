from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.main import db

class Node(db.Model):
  """ Model for storing node """
  __tablename__ = 'nodes'

  id = db.Column(db.Integer, primary_key=True)
  data_type = db.Column(db.String(500), nullable=False)
  data_type_id = db.Column(db.String(500), nullable=False, index=True)
  context = db.Column(JSONB(), default=[], nullable=False)
  data = db.Column(JSONB(), default=[], nullable=False)

  def to_dict(self):
    return {
      "id": self.id,
      "data_type": self.data_type,
      "data_type_id": self.data_type_id,
      "context": self.context,
      "data": self.data,
    }

  __table_args__ = (
      db.Index('node_id_constraint', data_type, data_type_id, unique=True),
  )