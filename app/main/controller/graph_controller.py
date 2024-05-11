from flask import request, current_app as app
from flask_restx import Resource, Namespace, fields
from app.main.lib.fields import JsonObject
import json
import numpy as np

from app.main.model.graph import Graph

api = Namespace('graph', description='graph operations')

graph_request = api.model('graph', {
    'threshold': fields.Float(required=True, description='threshold to be used for creating ties between edges'),
    'data_types': fields.List(required=True, description='data types to be employed in the graph - can be any of ["image", "audio", "text", "video"]', cls_or_instance=fields.String),
    'context': JsonObject(required=True, description='context dictionary for what critera to match on graph')
})

graph_fetch = api.model('graph', {
    'graph_id': fields.Integer(required=True, description='graph ID corresponding to a graph in the database.'),
})

@api.route('/')
class GraphController(Resource):
    @api.response(200, 'graph successfully created')
    @api.doc('Request a new graph')
    @api.expect(graph_request, validate=True)
    def post(self):
      graph_id, job_id = Graph.store(request.json)
      return {"graph_id": graph_id, "job_id": job_id}

    @api.response(200, 'graph successfully created')
    @api.doc('Load an existing graph')
    @api.expect(graph_fetch, validate=True)
    def get(self):
      return Graph.fetch(request.json)
