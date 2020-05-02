from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import helpers, Elasticsearch, TransportError
import json
import numpy as np
from app.main.lib.shared_models.shared_model import SharedModel

api = Namespace('model', description='model operations')

model_vector_request = api.model('model_vector_request', {
    'text': fields.String(required=True, description='text to be converted to a vector'),
    'model': fields.String(required=True, description='model to be used')
})

model_similarity_request = api.model('model_similarity_request', {
    'vector1': fields.String(required=True, description='the first vector, as a JSON list'),
    'vector2': fields.String(required=True, description='the second vector, as a JSON list'),
    'model': fields.String(required=True, description='model to be used')
})

@api.route('/')
class ModelVectorResource(Resource):
    @api.response(200, 'successfully retrieved list of running models.')
    @api.doc('Retrieve list of running models')
    def get(self):
        return {
            'models': SharedModel.get_servers()
        }

@api.route('/vector')
class ModelVectorResource(Resource):
    @api.response(200, 'text successfully converted to vector.')
    @api.doc('Convert a text to a vector')
    @api.expect(model_vector_request, validate=True)
    def post(self):
        model = SharedModel.get_client(request.json['model'])
        vector = model.get_shared_model_response(request.json['text'])
        return {
            'vector': json.dumps(vector)
        }

@api.route('/similarity')
class ModelSimilarityResource(Resource):
    @api.response(200, 'two vectors compared successfully.')
    @api.doc('Given two vectors, compare the similarities between them')
    @api.expect(model_similarity_request, validate=True)
    def post(self):
        model = SharedModel.get_client(request.json['model'])
        vec1 = np.asarray(json.loads(request.json['vector1']))
        vec2 = np.asarray(json.loads(request.json['vector2']))
        return {
            'similarity': model.similarity(vec1, vec2)
        }
