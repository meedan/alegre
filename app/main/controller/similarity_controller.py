from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import helpers, Elasticsearch, TransportError
from ..fields import JsonObject

api = Namespace('similarity', description='similarity operations')
similarity_request = api.model('similarity_request', {
    'text': fields.String(required=True, description='text to be stored or to find a similar one'),
    'context': JsonObject(required=False, description='context')
})

@api.route('/')
class SimilarityResource(Resource):
    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        result = es.index(
            body=request.json,
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
        es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
        conditions = [
            {
                'more_like_this': {
                    'fields': ['text'],
                    'like': request.json['text'],
                    'min_doc_freq': 1,
                    'min_term_freq': 1,
                    'max_query_terms': 12
                }
            },
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
        result = es.search(
            body={
                'query': {
                    'bool': {
                        'must': conditions
                    }
                }
            },
            doc_type='_doc',
            index=app.config['ELASTICSEARCH_SIMILARITY']
        )
        result = result['hits']['hits']
        return {
            'result': result
        }
