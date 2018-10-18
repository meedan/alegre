from flask import request
from flask_restplus import Resource, Namespace, fields
import langid

api = Namespace('langid', description='langid operations')
langid_request = api.model('langid_request', {
    'text': fields.String(required=True, description='text to identify')
})

@api.route('/')
class LangidResource(Resource):
    @api.response(201, 'langid successfully queried.')
    @api.doc('Make a langid query')
    @api.expect(langid_request, validate=True)
    def post(self):
        result = langid.classify(request.json['text'])
        return {
            'language': result[0],
            'confidence': result[1]
        }
