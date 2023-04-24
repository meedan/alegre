import copy
from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
from app.main.lib.fields import JsonObject
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.controller.bulk_similarity_controller import BulkSimilarityResource
from app.main.lib import similarity
from app.main.lib.text_similarity import get_document_body
from app.main.lib.elasticsearch import merge_contexts
def get_documents_by_ids(index, ids):
    query = {
        "query": {
            "ids": {
                "values": ids
            }
        }
    }
    response = es.search(index=index, body=query)
    documents = {hit['_id']: hit for hit in response['hits']['hits']}
    return documents

api = Namespace('bulk_update_similarity', description='bulk text similarity operations')
similarity_request = api.model('bulk_update_similarity_request', {
    'documents': fields.List(required=True, description='List of individual parameters typically sent to the similarity controller', cls_or_instance=JsonObject)
})
@api.route('/')
class BulkUpdateSimilarityResource(Resource):
    # Assumes less than 10k documents at a time.
    def get_bodies_for_request(self):
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=30)
        bodies_by_doc_id = {}
        existing_docs = get_documents_by_ids(app.config['ELASTICSEARCH_SIMILARITY'], [e.get("doc_id") for e in params.get("documents", [])])
        for document in request.json.get("documents", []):
            cleaned_document = similarity.get_body_for_text_document(document)
            for model_name in cleaned_document.get("models"):
                new_doc = copy.deepcopy(cleaned_document)
                new_doc["models"] = [model_name]
                if not bodies_by_doc_id.get(document.get("doc_id")):
                    bodies_by_doc_id[document.get("doc_id")] = existing_docs.get(document.get("doc_id", ""), {"_source": {}})["_source"]
                contexts = copy.deepcopy(merge_contexts(get_document_body(new_doc), existing_docs.get(document.get("doc_id", ""), {"_source": {}}))["contexts"])
                new_doc["contexts"] = contexts
                for key, value in get_document_body(new_doc).items():
                    bodies_by_doc_id[document.get("doc_id")][key] = value
        doc_ids = list(bodies_by_doc_id.keys())
        bodies = [bodies_by_doc_id.get(id) for id in doc_ids]
        return doc_ids, bodies
        
    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        doc_ids, bodies = self.get_bodies_for_request()
        return BulkSimilarityResource().submit_bulk_request(doc_ids, bodies)
