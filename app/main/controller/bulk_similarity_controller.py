from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
import elasticsearch
from app.main.lib.fields import JsonObject
from app.main.lib.elasticsearch import language_to_analyzer
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.controller.similarity_controller import SimilarityResource

api = Namespace('bulk_similarity', description='bulk text similarity operations')
similarity_request = api.model('bulk_similarity_request', {
    'documents': fields.List(required=True, description='List of individual parameters typically sent to the similarity controller', cls_or_instance=JsonObject)
})
@api.route('/')
class BulkSimilarityResource(Resource):
    def get_bodies_for_request(self):
        bodies = []
        doc_ids = []
        for document in request.json.get("documents", []):
            model_key = 'elasticsearch'
            if 'model' in document:
                model_key = document['model']
            es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
            body = { 'content': document['text'] }
            if model_key.lower() != 'elasticsearch':
                model = SharedModel.get_client(model_key)
                vector = model.get_shared_model_response(document['text'])
                body['vector_'+str(len(vector))] = vector
                body['model'] = model_key
            if 'context' in document:
                body['context'] = document['context']
            doc_ids.append(document.get("doc_id"))
            bodies.append(body)
        return doc_ids, bodies

    @api.response(200, 'text successfully deleted in the similarity database.')
    @api.doc('Delete a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def delete(self):
        results = []
        sim_controller = SimilarityResource()
        for doc in request.json["documents"]:
            results.append(sim_controller.delete_document(doc["doc_id"]))
        return results
        
    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        doc_ids, bodies = self.get_bodies_for_request()
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        results = []
        sim_controller = SimilarityResource()
        for doc_id, body in zip(doc_ids, bodies):
            results.append(sim_controller.store_document(body, doc_id))
        return results