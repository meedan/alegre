from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
import json

from app.main.lib.fields import JsonObject
from app.main.lib.elasticsearch import language_to_analyzer
from app.main.lib.shared_models.shared_model import SharedModel

api = Namespace('similarity', description='text similarity operations')
similarity_request = api.model('similarity_request', {
    'text': fields.String(required=True, description='text to be stored or queried for similarity'),
    'model': fields.String(required=False, description='similarity model to use: "elasticsearch" (pure Elasticsearch, default) or the key name of an active model'),
    'language': fields.String(required=False, description='language code for the analyzer to use during the similarity query (defaults to standard analyzer)'),
    'threshold': fields.Float(required=False, description='minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)'),
    'context': JsonObject(required=False, description='context')
})

@api.route('/')
class SimilarityResource(Resource):
    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        model_key = 'elasticsearch'
        if 'model' in request.json:
            model_key = request.json['model']
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        body = { 'content': request.json['text'] }
        if model_key.lower() != 'elasticsearch':
            model = SharedModel.get_client(model_key)
            body['vector'] = model.get_shared_model_response(request.json['text'])
            body['model'] = model_key
        if 'context' in request.json:
            body['context'] = request.json['context']
        result = es.index(
            body=body,
            doc_type='_doc',
            index=app.config['ELASTICSEARCH_SIMILARITY']
        )
        es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
        success = False
        if result['result'] == 'created':
            success = True
        return {
            'success': success
        }

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
            conditions = [
                {
                    'function_score': {
                        'min_score': threshold,
                        'query': {
                            'match_all': {}
                        },
                        'functions': [
                            {
                                'script_score': {
                                    'script': {
                                        'source': 'cosine',
                                        'lang': 'meedan_scripts',
                                        'params': {
                                            'vector': vector,
                                            'model': model_key
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ]

            # Add model to be matched.
            conditions.append(
                {
                    'match': {
                        'model': {
                          'query': model_key,
                        }
                    }
                },
            )

        if 'context' in request.json:
            matches = []
            for key in request.json['context']:
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
            conditions.append(context)

        app.logger.info("***** ES conditions: %s", json.dumps(conditions))

        body = {
            'query': {
                'bool': {
                    'must': conditions
                }
            }
        }
        result = es.search(
            body=body,
            doc_type='_doc',
            index=app.config['ELASTICSEARCH_SIMILARITY']
        )
        return {
            'result': result['hits']['hits']
        }
