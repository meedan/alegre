from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
import elasticsearch
from app.main.lib.fields import JsonObject
from app.main.lib.elasticsearch import language_to_analyzer
from app.main.lib.shared_models.shared_model import SharedModel

api = Namespace('bulk_similarity', description='bulk text similarity operations')
similarity_request = api.model('bulk_similarity_request', {
    'documents': fields.List(required=True, description='List of individual parameters typically sent to the similarity controller', cls_or_instance=JsonObject)
})
@api.route('/')
class SimilarityResource(Resource):
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
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        results = []
        for doc in request.json["documents"]:
            results.append(es.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc["doc_id"]))
        return results
        
    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        doc_ids, bodies = self.get_bodies_for_request()
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        results = []
        for doc_id, body in zip(doc_ids, bodies):
            app.logger.debug("Body is:")
            app.logger.debug(body)
            if doc_id:
                app.logger.debug("DOC ID PASSED")
                try:
                    found_doc = es.get(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc_id)
                except elasticsearch.exceptions.NotFoundError:
                    found_doc = None
                app.logger.debug(found_doc)
                if found_doc:
                    result = es.update(
                        id=doc_id,
                        body={"doc": body},
                        index=app.config['ELASTICSEARCH_SIMILARITY']
                    )
                else:
                    result = es.index(
                        id=doc_id,
                        body=body,
                        index=app.config['ELASTICSEARCH_SIMILARITY']
                    )
            else:
                result = es.index(
                    body=body,
                    index=app.config['ELASTICSEARCH_SIMILARITY']
                )
            app.logger.debug(result)
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            success = False
            if result['result'] == 'created' or result['result'] == 'updated':
                success = True
            results.append({
                'doc_id': doc_id,
                'success': success
            })
        return results