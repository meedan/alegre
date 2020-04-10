from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import helpers, Elasticsearch, TransportError
import json
import numpy as np
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.math_helpers import similarity_for_model_name

api = Namespace('wordvec', description='word vector operations')

wordvec_vector_request = api.model('wordvec_vector_request', {
    'text': fields.String(required=True, description='text to be converted to a vector'),
})

wordvec_similarity_request = api.model('wordvec_similarity_request', {
    'vector1': fields.String(required=True, description='the first vector, as a JSON list'),
    'vector2': fields.String(required=True, description='the second vector, as a JSON list'),
})

@api.route('/vector')
class WordVecVectorResource(Resource):
    @api.response(200, 'text successfully converted to vector.')
    @api.doc('Convert a text to a vector')
    @api.expect(wordvec_vector_request, validate=True)
    def post(self):
        model = SharedModel.get_client(request.json.get("model"))
        vector = model.get_shared_model_response(request.json['text'])
        return {
            'vector': json.dumps(vector)
        }

@api.route('/similarity')
class WordVecSimilarityResource(Resource):
    @api.response(200, 'two vectors compared successfully.')
    @api.doc('Given two vectors, compare the similarities between them')
    @api.expect(wordvec_similarity_request, validate=True)
    def post(self):
        vec1 = np.asarray(json.loads(request.json['vector1']))
        vec2 = np.asarray(json.loads(request.json['vector2']))
        model_name = request.json.get("model_name")
        model = SharedModel.get_client(model_name)
        return {
            'similarity': similarity_for_model_name(model_name, vec1, vec2)
        }
