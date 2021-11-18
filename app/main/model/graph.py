from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.main import db

class Graph(db.Model):
  """ Model for storing graphs """
  __tablename__ = 'graphs'

  id = db.Column(db.Integer, primary_key=True)
  threshold = db.Column(db.Float, nullable=False)
  data_types = db.Column(ARRAY(db.String(255, convert_unicode=True)), nullable=True)
  status = db.Column(db.String(255, convert_unicode=True), nullable=True)
  context = db.Column(JSONB(), default=[], nullable=False)

  def set_status(self, status):
    graph.status = status
    db.sesion.commit()
    
  @classmethod
  def enrich(cls, graph_id):
    graph = Graph.query.get(graph_id)
    graph.set_status("enriching")
    db.sesion.commit()
    for data_type in data_types:
      graph.generate_edges_for_type(data_type)
    graph.set_status("enriched")

  @classmethod
  def store(cls, request):
    graph = Graph(threshold=request.json["threshold"], data_types=request.json["data_types"], context=request.json["context"], status="created")
    db.session.add(graph)
    #todo add to queue, call via Graph.enrich(graph.id)
    return graph.id

  @classmethod
  def fetch(cls, request):
    return [edge.to_dict() for edge in graph.edges]
      