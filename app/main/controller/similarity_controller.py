from datetime import datetime
from flask import request, current_app as app
from flask import abort, jsonify
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
from app.main.lib.shared_models.shared_model import SharedModel

from app.main.lib.fields import JsonObject
from app.main.lib import similarity

api = Namespace('similarity', description='text similarity operations')
similarity_request = api.model('similarity_request', {
    'text': fields.String(required=False, description='text to be stored or queried for similarity'),
    'doc_id': fields.String(required=False, description='text ID to constrain uniqueness'),
    'model': fields.String(required=False, description='similarity model to use: "elasticsearch" (pure Elasticsearch, default) or the key name of an active model'),
    'language': fields.String(required=False, description='language code for the analyzer to use during the similarity query (defaults to standard analyzer)'),
    'threshold': fields.Float(required=False, description='minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)'),
    'context': JsonObject(required=False, description='context'),
    'fuzzy': fields.Boolean(required=False, description='whether or not to use fuzzy search on GET queries (only used when model is set to \'elasticsearch\')'),
})
@api.route('/')
class SimilarityResource(Resource):
    def get_body_for_request(self):
        model_key = 'elasticsearch'
        if 'model' in request.json:
            model_key = request.json['model']
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        body = { 'content': request.json['text'] }
        if model_key.lower() != 'elasticsearch':
            model = SharedModel.get_client(model_key)
            vector = model.get_shared_model_response(request.json['text'])
            body['vector_'+str(len(vector))] = vector
            body['model'] = model_key
            body['created_at'] = request.json.get("created_at", datetime.now())
        if 'context' in request.json:
            body['context'] = request.json['context']
        return body

    @api.response(200, 'text successfully deleted in the similarity database.')
    @api.doc('Delete a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def delete(self):
        doc_id = request.json.get("doc_id")
        response = similarity.delete_item(request.json, "text")
        if response == False:
            abort(404, description=f"Doc Not Found for id {doc_id}! No Deletion Occurred.")
        else:
            return response

    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        doc_id = request.json.get("doc_id")
        item = self.get_body_for_request()
        item["doc_id"] = doc_id
        return similarity.add_item(item, "text")

    @api.response(200, 'text similarity successfully queried.')
    @api.doc('Make a text similarity query')
    @api.doc(params={'text': 'text to be stored or queried for similarity', 'threshold': 'minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)', 'model': 'similarity model to use: "elasticsearch" (pure Elasticsearch, default) or the key name of an active model'})
    def get(self):
      return similarity.get_similar_items(request.args or request.json, "text")
