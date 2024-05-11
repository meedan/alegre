from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship, backref
from app.main import db
class Edge(db.Model):
  """ Model for storing edges """
  __tablename__ = 'edges'

  id = db.Column(db.Integer, primary_key=True)
  graph_id = db.Column(db.Integer, db.ForeignKey('graphs.id'), index=True)
  graph = db.relationship("Graph", backref=backref("edges", cascade="all, delete-orphan"))
  source_id = db.Column(db.Integer, db.ForeignKey('nodes.id'))
  source_context = db.Column(JSONB(), default={}, nullable=False)
  source = relationship("Node", foreign_keys=[source_id])
  target_id = db.Column(db.Integer, db.ForeignKey('nodes.id'))
  target_context = db.Column(JSONB(), default={}, nullable=False)
  target = relationship("Node", foreign_keys=[target_id])
  edge_type = db.Column(db.String(500), nullable=False)
  edge_weight = db.Column(db.Float, nullable=False)
  edge_context = db.Column(JSONB(), default={}, nullable=False)
  context = db.Column(JSONB(), default={}, nullable=False)

  __table_args__ = (
      db.Index('edge_source_target_graph', source_id, target_id, graph_id, unique=True),
  )

  def to_dict(self):
    return {
      "id": self.id,
      "graph_id": self.graph_id,
      "source_id": self.source_id,
      "source_context": self.source_context,
      "target_id": self.target_id,
      "target_context": self.target_context,
      "edge_type": self.edge_type,
      "edge_weight": self.edge_weight,
      "edge_context": self.edge_context,
      "context": self.context,
    }
