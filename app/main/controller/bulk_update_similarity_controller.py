from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import elasticsearch
from app.main.lib.fields import JsonObject
from app.main.lib.elasticsearch import language_to_analyzer
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.controller.bulk_similarity_controller import BulkSimilarityResource

api = Namespace('bulk_update_similarity', description='bulk text similarity operations')
similarity_request = api.model('bulk_update_similarity_request', {
    'documents': fields.List(required=True, description='List of individual parameters typically sent to the similarity controller', cls_or_instance=JsonObject)
})
def each_slice(list, size):
    batch = 0
    while batch * size < len(list):
        yield list[batch * size:(batch + 1) * size]
        batch += 1

@api.route('/')
class BulkUpdateSimilarityResource(Resource):
    def get_bulk_write_object(self, doc_id, body):
        return dict(
            **{'_op_type': 'update', '_index': app.config['ELASTICSEARCH_SIMILARITY'], '_type': '_doc', '_id': doc_id},
            **body
        )

    def get_bodies_for_request(self):
        bodies = []
        doc_ids = []
        for document in request.json.get("documents", []):
            es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
            body = {'model': document['model']}
            model = SharedModel.get_client(document['model'])
            vector = model.get_shared_model_response(document['text'])
            body['vector_'+str(len(vector))] = vector
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
        return BulkSimilarityController().submit_bulk_request(doc_ids, bodies)
