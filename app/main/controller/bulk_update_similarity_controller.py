from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from app.main.lib.fields import JsonObject

from app.main.controller.bulk_similarity_controller import BulkSimilarityResource
from app.main.controller.bulk_similarity_controller import json_parse_timestamp
from app.main.lib.text_similarity import get_document_body

api = Namespace('bulk_update_similarity', description='bulk text similarity operations')
similarity_request = api.model('bulk_update_similarity_request', {
    'documents': fields.List(required=True, description='List of individual parameters typically sent to the similarity controller', cls_or_instance=JsonObject)
})
@api.route('/')
class BulkUpdateSimilarityResource(Resource):
    def get_bodies_for_request(self):
        bodies = []
        doc_ids = []
        for document in request.json.get("documents", []):
            doc_ids.append(document.get("doc_id"))
            bodies.append(json_parse_timestamp(get_document_body(similarity.get_body_for_text_document(document))))
        return doc_ids, bodies
        
    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        doc_ids, bodies = self.get_bodies_for_request()
        return BulkSimilarityResource().submit_bulk_request(doc_ids, bodies)
