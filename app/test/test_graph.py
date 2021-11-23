import igraph
import unittest
import json
from flask import current_app as app
from unittest.mock import patch
import numpy as np

from app.test.base import BaseTestCase
from app.main.model.graph import Graph
from app.main.model.edge import Edge
from app.main.model.node import Node
from app.main.lib.graph_writer import generate_edges_for_type
g = igraph.Graph.GRG(100, 0.07)
mapped = {}
for edge in g.es:
  if not mapped.get(edge.source):
    mapped[edge.source] = []
  mapped[edge.source].append(edge.target)

def get_iterable_objects(graph, data_type):
  return [{"id": n.index, "context": {"blah": 1, "project_media_id": n.index}} for n in g.vs]

def get_matches_for_item(graph, item, data_type):
  return [{"id": e, "context": {"blah": 1, "project_media_id": e}, "score": np.random.random()*0.2 + 0.8} for e in mapped.get(item["id"], [])]

class TestGraph(BaseTestCase):
  def test_graphs_can_be_written_and_read(self):
    graph_id = Graph.store({"threshold": 0.8, "data_types": ["image"], "context": {"blah": 1}})
    self.assertIsInstance(graph_id, int)
    graph = Graph.enrich(graph_id, get_iterable_objects, get_matches_for_item)
    self.assertIsInstance(graph, Graph)
    graph_response = Graph.fetch({"graph_id": graph_id})
    self.assertIsInstance(graph_response, list)
    self.assertIsInstance(graph_response[0], list)
    self.assertIsInstance(graph_response[0][0], dict)
    response = self.client.get('/graph/', data=json.dumps({
        'graph_id': graph_id,
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertIsInstance(result, dict)
    self.assertIsInstance(result["clusters"], list)
    self.assertIsInstance(result["clusters"][0], list)
    self.assertIsInstance(result["clusters"][0][0], dict)

  def test_graph_endpoints(self):
    response = self.client.post('/graph/', data=json.dumps({
      "threshold": 0.8,
      "data_types": ["image"],
      "context": {"blah": 1}
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertIsInstance(result, dict)
    self.assertIsInstance(result["graph_id"], int)
    graph = Graph.enrich(result["graph_id"], get_iterable_objects, get_matches_for_item)
    response = self.client.get('/graph/', data=json.dumps({
        'graph_id': result["graph_id"],
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertIsInstance(result, dict)
    self.assertIsInstance(result["clusters"], list)
    self.assertIsInstance(result["clusters"][0], list)
    self.assertIsInstance(result["clusters"][0][0], dict)

if __name__ == '__main__':
    unittest.main()
