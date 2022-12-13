from flask import request, current_app as app
from flask_restx import Resource, Namespace, fields
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from app.main.lib.fields import JsonObject
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.text_similarity import get_document_body
from app.main.lib import similarity

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
            doc_ids.append(document.get("doc_id"))
            bodies.append(get_document_body(similarity.get_body_for_text_document(document)))
        return doc_ids, bodies
        
    def submit_bulk_request(self, doc_ids, bodies):
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        writables = []
        for doc_body_set in each_slice(list(zip(doc_ids, bodies)), 8000):
            to_write = []
            for doc_id, body in doc_body_set:
                to_write.append(self.get_bulk_write_object(doc_id, body))
                writables.append(to_write[-1])
            helpers.bulk(es, to_write)
        return writables

    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        doc_ids, bodies = self.get_bodies_for_request()
        return self.submit_bulk_request(doc_ids, bodies)
