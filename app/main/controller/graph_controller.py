from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
import json
import numpy as np

api = Namespace('graph', description='graph operations')

model_vector_request = api.model('graph', {
    'threshold': fields.Float(required=True, description='threshold to be used for creating ties between edges'),
    'data_types': fields.List(required=True, description='data types to be employed in the graph - can be any of ["image", "audio", "text", "video"]'),
    'context': fields.Arbitrary(required=True, description='context dictionary for what critera to match on graph')
})
  threshold = db.Column(db.Float, nullable=False)
  data_types = db.Column(ARRAY(db.String(255, convert_unicode=True)), nullable=True)
  status = db.Column(db.String(255, convert_unicode=True), nullable=True)
  context = db.Column(JSONB(), default=[], nullable=False)

@api.route('/graph')
class Graph(Resource):
    @api.response(200, 'graph successfully created')
    @api.doc('Request a new graph')
    @api.expect(request, validate=True)
    def post(self):
      return {"graph_id": Graph.store(request)}

    @api.response(200, 'graph successfully created')
    @api.doc('Load an existing graph')
    @api.expect(request, validate=True)
    def get(self):
      return {"edges": Graph.fetch(request)}
