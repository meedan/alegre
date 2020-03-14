from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from elasticsearch import helpers, Elasticsearch, TransportError
from app.main.lib.fields import JsonObject

api = Namespace('glossary', description='glossary operations')
glossary_request = api.model('glossary_request', {
  'en': fields.String(required=False, description='english term'),
  'pt': fields.String(required=False, description='portuguese term'),
  'ar': fields.String(required=False, description='arabic term'),
  'context': JsonObject(required=False, description='context')
  })

@api.route('/')
class GlossaryResource(Resource):
  @api.response(200, 'glossary successfully stored.')
  @api.doc('Store a glossary entry')
  @api.expect(glossary_request, validate=True)
  def post(self):
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
    result = es.index(
      body=request.json,
      doc_type='_doc',
      index=app.config['ELASTICSEARCH_GLOSSARY']
      )
    es.indices.refresh(index=app.config['ELASTICSEARCH_GLOSSARY'])
    return {
    'result': result
    }

    @api.response(200, 'glossary successfully queried.')
    @api.doc('Make a glossary query')
    @api.expect(glossary_request, validate=True)
    def get(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      result = es.search(
        body=request.json,
        doc_type='_doc',
        index=app.config['ELASTICSEARCH_GLOSSARY']
        )
      return {
      'result': result
      }
