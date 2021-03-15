from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
import elasticsearch
from app.main.lib.fields import JsonObject
from app.main.lib.elasticsearch import language_to_analyzer
from app.main.lib.shared_models.shared_model import SharedModel

api = Namespace('similarity', description='text similarity operations')
similarity_request = api.model('similarity_request', {
    'text': fields.String(required=False, description='text to be stored or queried for similarity'),
    'doc_id': fields.String(required=False, description='text ID to constrain uniqueness'),
    'model': fields.String(required=False, description='similarity model to use: "elasticsearch" (pure Elasticsearch, default) or the key name of an active model'),
    'language': fields.String(required=False, description='language code for the analyzer to use during the similarity query (defaults to standard analyzer)'),
    'threshold': fields.Float(required=False, description='minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)'),
    'context': JsonObject(required=False, description='context')
})
@api.route('/')
class SimilarityResource(Resource):
    def store_document(self, body, doc_id):
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        if doc_id:
            try:
                found_doc = es.get(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc_id)
            except elasticsearch.exceptions.NotFoundError:
                found_doc = None
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
        es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
        success = False
        if result['result'] == 'created' or result['result'] == 'updated':
            success = True
        return {
            'success': success
        }

    def delete_document(self, doc_id):
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        return es.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc_id)

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
        if 'context' in request.json:
            body['context'] = request.json['context']
        return body

    @api.response(200, 'text successfully deleted in the similarity database.')
    @api.doc('Delete a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def delete(self):
        return self.delete_document(request.json["doc_id"])

    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        return self.store_document(
            self.get_body_for_request(),
            request.json.get("doc_id")
        )

    @api.response(200, 'text similarity successfully queried.')
    @api.doc('Make a text similarity query')
    @api.expect(similarity_request, validate=True)
    def get(self):
        model_key = 'elasticsearch'
        if 'model' in request.json:
            model_key = request.json['model']
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=30)
        conditions = []
        threshold = 0.9
        if 'threshold' in request.json:
            threshold = request.json['threshold']

        if model_key.lower() == 'elasticsearch':
            conditions = [
                {
                    'match': {
                      'content': {
                          'query': request.json['text'],
                          'minimum_should_match': str(int(round(threshold * 100))) + '%'
                      }
                    }
                },
            ]

            # FIXME: `analyzer` and `minimum_should_match` don't play well together.
            if 'language' in request.json:
                conditions[0]['match']['content']['analyzer'] = language_to_analyzer(request.json['language'])
                del conditions[0]['match']['content']['minimum_should_match']

        else:
            model = SharedModel.get_client(model_key)
            vector = model.get_shared_model_response(request.json['text'])
            conditions = {
                'query': {
                    'script_score': {
                        'min_score': threshold,
                        'query': {
                            'bool': {
                                'must': [
                                    {
                                        'match': {
                                            'model': {
                                              'query': model_key,
                                            }
                                        }
                                    }
                                ]
                            }
                        },
                        'script': {
                            'source': "cosineSimilarity(params.query_vector, 'vector_"+str(len(vector))+"') + 1.0", 
                            'params': {
                                'query_vector': vector
                            }
                        }
                    }
                }
            }

        if 'context' in request.json:
            matches = []
            for key in request.json['context']:
                if isinstance(request.json['context'][key], list):
                    matches.append({
                        'query_string': { 'query': str.join(" OR ", [f"context.{key}: {v}" for v in request.json['context'][key]])}
                    })
                else:
                    matches.append({
                        'match': { 'context.' + key: request.json['context'][key] }
                    })
            context = {
                'nested': {
                    'score_mode': 'none',
                    'path': 'context',
                    'query': {
                        'bool': {
                            'must': matches
                        }
                    }
                }
            }
            if isinstance(conditions, list):
                conditions.append(context)
            else:
                conditions['query']['script_score']['query']['bool']['must'].append(context)

        if isinstance(conditions, list):
            body = {
                'query': {
                    'bool': {
                        'must': conditions
                    }
                }
            }
        else:
            body = conditions

        result = es.search(
            body=body,
            index=app.config['ELASTICSEARCH_SIMILARITY']
        )
        return {
            'result': result['hits']['hits']
        }

