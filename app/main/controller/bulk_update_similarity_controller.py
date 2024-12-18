import copy
from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from opensearchpy import OpenSearch
from app.main.lib.fields import JsonObject
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.controller.bulk_similarity_controller import BulkSimilarityResource
from app.main.lib import similarity
from app.main.lib.text_similarity import get_document_body
from app.main.lib.opensearch import merge_contexts
def get_documents_by_ids(index, ids, es):
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

def merge_key_list(existing, new_values):
    if not existing:
        existing = []
    for v in new_values:
        if v not in existing:
            existing.append(v)
    return existing

def get_merged_contexts(tmp_doc, existing_doc):
    return copy.deepcopy(merge_contexts(get_document_body(tmp_doc), {"_source": existing_doc})["contexts"])

def update_existing_doc_values(document, existing_doc):
    cleaned_document = similarity.get_body_for_text_document(document, mode='store')
    for model_name in cleaned_document.get("models"):
        tmp_doc = copy.deepcopy(cleaned_document)
        tmp_doc["models"] = [model_name]
        tmp_doc["contexts"] = get_merged_contexts(tmp_doc, existing_doc)
        for key, value in get_document_body(tmp_doc).items():
            if key in ["models", "contexts"]:
                existing_doc[key] = merge_key_list(existing_doc.get(key, []), value)
            else:
                existing_doc[key] = value
    return existing_doc

def sorted_values(cases):
    doc_ids = list(cases.keys())
    values = [cases.get(doc_id) for doc_id in doc_ids]
    return doc_ids, values

def can_add_to_bodies(existing_doc, updateable):
    return (updateable and existing_doc) or (not updateable and not existing_doc)

def get_cases(params, existing_docs, updateable=True):
    bodies_by_doc_id = {}
    for document in params.get("documents", []):
        doc_id = document.get("doc_id")
        existing_doc = existing_docs.get(doc_id, {})
        if can_add_to_bodies(existing_doc, updateable):
            if not bodies_by_doc_id.get(doc_id):
                bodies_by_doc_id[doc_id] = existing_doc.get("_source", {})
            bodies_by_doc_id[doc_id] = update_existing_doc_values(document, bodies_by_doc_id[doc_id])
    return sorted_values(bodies_by_doc_id)

api = Namespace('bulk_update_similarity', description='bulk text similarity operations')
similarity_request = api.model('bulk_update_similarity_request', {
    'documents': fields.List(required=True, description='List of individual parameters typically sent to the similarity controller', cls_or_instance=JsonObject)
})
@api.route('/')
class BulkUpdateSimilarityResource(Resource):
    # Assumes less than 10k documents at a time.
    def get_writeable_data_for_request(self):
        es = OpenSearch(app.config['OPENSEARCH_URL'], timeout=30)
        params = request.json
        existing_docs = get_documents_by_ids(app.config['OPENSEARCH_SIMILARITY'], [e.get("doc_id") for e in params.get("documents", [])], es)
        updated_cases = get_cases(params, existing_docs)
        new_cases = get_cases(params, existing_docs, False)
        return updated_cases, new_cases
        
    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        updated_cases, new_cases = self.get_writeable_data_for_request()
        response = [
            BulkSimilarityResource().submit_bulk_request(updated_cases[0], updated_cases[1], "update"),
            BulkSimilarityResource().submit_bulk_request(new_cases[0], new_cases[1])
        ]
        all_written = []
        for response_data in response:
            for row in response_data:
                row["_source"].pop("created_at", None)
                all_written.append(row)
        return all_written
