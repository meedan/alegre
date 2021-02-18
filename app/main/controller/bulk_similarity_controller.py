from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import elasticsearch
from app.main.lib.fields import JsonObject
from app.main.lib.elasticsearch import language_to_analyzer
from app.main.lib.shared_models.shared_model import SharedModel

api = Namespace('bulk_similarity', description='bulk text similarity operations')
similarity_request = api.model('bulk_similarity_request', {
    'documents': fields.List(required=True, description='List of individual parameters typically sent to the similarity controller', cls_or_instance=JsonObject)
})
def each_slice(list, size):
    batch = 0
    while batch * size < len(list):
        yield list[batch * size:(batch + 1) * size]
        batch += 1

@api.route('/')
class BulkSimilarityResource(Resource):
    def get_bulk_write_object(self, doc_id, body):
        return dict(
            **{'_index': app.config['ELASTICSEARCH_SIMILARITY'], '_type': '_doc', '_id': doc_id},
            **body
        )

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
        
    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        doc_ids, bodies = self.get_bodies_for_request()
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        results = []
        for doc_body_set in each_slice(list(zip(doc_ids, bodies)), 8000):
            to_write = []
            for doc_id, body in doc_body_set:
                to_write.append(self.get_bulk_write_object(doc_id, body))
            results.append(helpers.bulk(es, to_write))
        return results