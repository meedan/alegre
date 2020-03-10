from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
from app.main import ds
from app.main.lib.fields import JsonObject
from app.main.lib.elasticsearch import language_to_analyzer

api = Namespace('similarity', description='text similarity operations')
similarity_request = api.model('similarity_request', {
    'text': fields.String(required=True, description='text to be stored or queried for similarity'),
    'method': fields.String(required=False, description='similarity method to use: "elasticsearch" (pure ElasticSearch, default) or "wordvec" (Word2Vec plus ElasticSearch)'),
    'language': fields.String(required=False, description='language code for the analyzer to use during the similarity query (defaults to standard analyzer)'),
    'threshold': fields.Float(required=False, description='minimum score to consider, between 0 and 1 (defaults to 0.7)'),
    'context': JsonObject(required=False, description='context')
})

@api.route('/')
class SimilarityResource(Resource):
    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        similarity_type = 'elasticsearch'
        if 'method' in request.json:
            similarity_type = request.json['method']
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        body = { 'content': request.json['text'] }
        if similarity_type == 'wordvec':
            body['vector'] = ds.vectorize(request.json['text']).tolist()
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
        similarity_type = 'elasticsearch'
        if 'method' in request.json:
            similarity_type = request.json['method']
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=30)
        conditions = []

        threshold = 0.7
        if 'threshold' in request.json:
            threshold = request.json['threshold']

        if similarity_type == 'elasticsearch':
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
            if 'language' in request.json:
                conditions[0]['match']['content']['analyzer'] = language_to_analyzer(request.json['language'])
                del conditions[0]['match']['content']['minimum_should_match']

        elif similarity_type == 'wordvec':
            vector = ds.vectorize(request.json['text']).tolist()
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
                                            'vector': vector
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
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
