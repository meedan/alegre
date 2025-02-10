import unittest
import json
import uuid
from flask import current_app as app
from unittest.mock import patch
from collections import namedtuple

import igraph
import numpy as np
import rq

from app.main import db
from app.test.base import BaseTestCase
from app.main.model.graph import Graph
from app.main.model.edge import Edge
from app.main.model.node import Node
from app.main.model.video import Video
from app.main.model.image import ImageModel
from app.main.model.audio import Audio
from app.main.lib.graph_writer import get_iterable_objects, get_matches_for_item, generate_edges_for_type
g = igraph.Graph.GRG(100, 0.07)
mapped = {}
for edge in g.es:
  if not mapped.get(edge.source):
    mapped[edge.source] = []
  mapped[edge.source].append(edge.target)

def tmp_get_iterable_objects(graph, data_type):
  return [{"id": n.index, "context": {"blah": 1, "project_media_id": n.index}} for n in g.vs]

def tmp_get_matches_for_item(graph, item, data_type):
  return [{"id": e, "context": {"blah": 1, "project_media_id": e}, "score": np.random.random()*0.2 + 0.8} for e in mapped.get(item["id"], [])]

Job = namedtuple('Job', ('id'))

class TestGraph(BaseTestCase):
  def test_models_return_correct_iterables(self):
    context = {"team_id": [1,2,4]}
    for data_type, model in [["video", Video], ["image", ImageModel], ["audio", Audio]]:
      for i in range(4):
        params = {"doc_id": f"blah_{i}", "url": f"https://blah.com/{data_type}/{i}", "context": [{"team_id": i+1}]}
        if data_type == "image":
          params["sha256"] = f"blah_{i}"
          params["phash"] = 101011101010110101
        obj = model(**params)
        db.session.add(obj)
        db.session.commit()
      graph = Graph(context=context)
      matched_team_ids = sorted([e for i in [[ee.get("team_id") for ee in e.context] for e in get_iterable_objects(graph, data_type)] for e in i])
      self.assertIsInstance(matched_team_ids, list)

  def test_graphs_can_be_written_and_read(self):
    with patch('app.main.model.graph.Graph.enqueue', ) as mock_enqueue:
      mock_enqueue.return_value = Job(str(uuid.uuid1()))
      graph_id, job_id = Graph.store({"threshold": 0.8, "data_types": ["image"], "context": {"blah": 1}})
      self.assertIsInstance(graph_id, int)
      graph = Graph.enrich(graph_id, tmp_get_iterable_objects, tmp_get_matches_for_item)
      self.assertIsInstance(graph, Graph)
      graph_response = Graph.fetch({"graph_id": graph_id})
      self.assertIsInstance(graph_response, dict)
      self.assertIsInstance(graph_response["graph"], dict)
      self.assertIsInstance(graph_response["clusters"][0], list)
      self.assertIsInstance(graph_response["clusters"][0][0], dict)
      response = self.client.get('/graph/cluster/', data=json.dumps({
          'graph_id': graph_id,
      }), content_type='application/json')
      result = json.loads(response.data.decode())
      self.assertIsInstance(result, dict)
      self.assertIsInstance(result["clusters"], list)
      self.assertIsInstance(result["clusters"][0], list)
      self.assertIsInstance(result["clusters"][0][0], dict)

  def test_graph_endpoints(self):
    with patch('app.main.model.graph.Graph.enqueue', ) as mock_enqueue:
      mock_enqueue.return_value = Job(str(uuid.uuid1()))
      response = self.client.post('/graph/cluster/', data=json.dumps({
        "threshold": 0.8,
        "data_types": ["image"],
        "context": {"blah": 1},
        "url": "https://blah.com/"
      }), content_type='application/json')
      result = json.loads(response.data.decode())
      self.assertIsInstance(result, dict)
      self.assertIsInstance(result["graph_id"], int)
      response = self.client.get('/graph/cluster/', data=json.dumps({
          'graph_id': result["graph_id"],
      }), content_type='application/json')
      result = json.loads(response.data.decode())
      self.assertIsInstance(result, dict)
      self.assertIsInstance(result["clusters"], list)
      self.assertIsInstance(result["graph"], dict)
      self.assertEqual(result["graph"]["status"], "created")
      graph = Graph.enrich(result["graph"]["id"], tmp_get_iterable_objects, tmp_get_matches_for_item)
      item = {"url": "https://blah.com/", "context": graph.context, "threshold": graph.threshold}
      response = self.client.get('/graph/cluster/', data=json.dumps({
          'graph_id': result["graph"]["id"],
      }), content_type='application/json')
      result = json.loads(response.data.decode())
      self.assertIsInstance(result, dict)
      self.assertIsInstance(result["clusters"], list)
      self.assertIsInstance(result["clusters"][0], list)
      self.assertIsInstance(result["clusters"][0][0], dict)
      self.assertIsInstance(result["graph"], dict)
      self.assertEqual(result["graph"]["status"], "enriched")

  def test_graph_text_type(self):
    response = self.client.post('/graph/cluster/', data=json.dumps({
      "threshold": 0.8,
      "data_types": ["text"],
      "context": {"blah": 1},
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    response = self.client.get('/graph/cluster/', data=json.dumps({
        'graph_id': result["graph_id"],
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertIsInstance(result, dict)
    self.assertIsInstance(result["clusters"], list)
    self.assertIsInstance(result["graph"], dict)
    self.assertEqual(result["graph"]["status"], "created")
    graph = Graph.enrich(result["graph"]["id"], get_iterable_objects, tmp_get_matches_for_item)
    response = self.client.get('/graph/cluster/', data=json.dumps({
        'graph_id': 2,
    }), content_type='application/json')
    item = {}
    result = json.loads(response.data.decode())
    self.assertIn('error', result)
    self.assertEqual(result["error"], "Graph with id of 2 not found!")


if __name__ == '__main__':
    unittest.main()
