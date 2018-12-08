from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import helpers, Elasticsearch, TransportError
from app.main import ds
from ..fields import JsonObject

api = Namespace('similarity', description='similarity operations')
similarity_request = api.model('similarity_request', {
    'text': fields.String(required=True, description='text to be stored or to find a similar one'),
    'type': fields.String(required=False, description='which similarity to use: "es" (pure ElasticSearch, default) or "wordvec" (Word2Vec plus ElasticSearch)'),
    'context': JsonObject(required=False, description='context')
})

@api.route('/')
class SimilarityResource(Resource):
    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        similarity_type = 'es'
        if 'type' in request.json:
            similarity_type = request.json['type']
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


@api.route('/query')
class SimilarityQueryResource(Resource):
    @api.response(200, 'similarity successfully queried.')
    @api.doc('Make a similarity query')
    @api.expect(similarity_request, validate=True)
    def post(self):
        similarity_type = 'es'
        if 'type' in request.json:
            similarity_type = request.json['type']
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        conditions = []
        if similarity_type == 'es':
            conditions = [
                {
                    'match': {
                      'content': {
                          'query': request.json['text'],
                          'minimum_should_match': '70%'
                      }
                    }
                },
            ]
        elif similarity_type == 'wordvec':
            vector = ds.vectorize(request.json['text']).tolist()
            conditions = [
                {
                    'function_score': {
                        'query': {
                            'match_all': {}
                        },
                        'boost': -1,
                        'boost_mode': 'sum',
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
            match = {}
            for key in request.json['context']:
                match['context.' + key] = request.json['context'][key]
            context = {
                'nested': {
                    'path': 'context',
                    'query': {
                        'bool': {
                            'must': [
                                {
                                    'match': match
                                }
                            ]
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
        result = result['hits']['hits']
        return {
            'result': result
        }
