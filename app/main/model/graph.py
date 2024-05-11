from sqlalchemy.dialects.postgresql import JSONB, ARRAY
import igraph
from rq import Queue
from flask import request, current_app as app
from dateutil import parser

from app.main.model.node import Node
from app.main import db
from app.main.lib.graph_writer import generate_edges_for_type, get_iterable_objects, get_matches_for_item
from app.main.lib.error_log import ErrorLog
from app.main.lib import redis_client

class Graph(db.Model):
  """ Model for storing graphs """
  __tablename__ = 'graphs'

  id = db.Column(db.Integer, primary_key=True)
  threshold = db.Column(db.Float, nullable=False)
  data_types = db.Column(ARRAY(db.String(255)), nullable=True)
  status = db.Column(db.String(255), nullable=True)
  start_time = db.Column(db.DateTime, nullable=True)
  end_time = db.Column(db.DateTime, nullable=True)
  context = db.Column(JSONB(), default=[], nullable=False)

  def to_dict(self):
    return {
      "id": self.id,
      "threshold": self.threshold,
      "data_types": self.data_types,
      "status": self.status,
      "context": self.context,
    }

  def nodes(self):
    return Node.query.filter(Node.id.in_([item for sublist in [[e.source_id, e.target_id] for e in self.edges] for item in sublist]))

  def set_status(self, status):
    self.status = status
    db.session.commit()
    
  def enqueue(self):
    redis_server = redis_client.get_client()
    queue = Queue(connection=redis_server, default_timeout=60*60*24)
    job = queue.enqueue(Graph.enrich, self.id)
    return job
    
  @classmethod
  def enrich(cls, graph_id, item_iterator=get_iterable_objects, match_resolver=get_matches_for_item):
    try:
      graph = Graph.query.get(graph_id)
      graph.set_status("enriching")
      for data_type in graph.data_types:
        generate_edges_for_type(graph, data_type, item_iterator, match_resolver)
      graph.set_status("enriched")
      return graph
    except Exception as err:
      ErrorLog.notify(err)
      graph.set_status("errored")
      return graph

  @classmethod
  def store(cls, request_json):
    start_time = None
    end_time = None
    if request_json.get("start_date"):
      start_time = parser.parse(request_json.get("start_time"))
    if request_json.get("end_date"):
      end_time = parser.parse(request_json.get("end_time"))
    graph = Graph(threshold=request_json["threshold"], data_types=request_json["data_types"], context=request_json["context"], start_time=start_time, end_time=end_time, status="created")
    db.session.add(graph)
    db.session.commit()
    db.session.refresh(graph)
    job = graph.enqueue()
    return graph.id, job.id

  @classmethod
  def fetch(cls, request_json):
    graph = Graph.query.get(request_json.get("graph_id"))
    if graph:
      if graph.status == "enriched":
        graph_obj=igraph.Graph.TupleList([(e.source_id, e.target_id) for e in graph.edges])
        clustered_result = []
        for cluster in graph_obj.clusters():
          clustered_result.append(
            [n.to_dict() for n in Node.query.filter(Node.id.in_([v['name'] for v in graph_obj.vs(cluster)]))]
          )
        return {"clusters": clustered_result, "graph": graph.to_dict()}
      else:
        return {"clusters": [], "graph": graph.to_dict()}
    else:
      return {"error": "Graph with id of "+str(request_json.get("graph_id"))+" not found!"}