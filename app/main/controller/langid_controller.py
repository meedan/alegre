from flask import request
from flask_restplus import Resource, Namespace, fields
from google.cloud import translate

api = Namespace('langid', description='langid operations')
langid_request = api.model('langid_request', {
    'text': fields.String(required=True, description='text to identify')
})

@api.route('/')
class LangidResource(Resource):
    @api.response(200, 'langid successfully queried.')
    @api.doc('Identify the language of a text document')
    @api.expect(langid_request, validate=True)
    def post(self):
        client = translate.Client.from_service_account_json('./google_credentials.json')
        result = client.detect_language([request.json['text']])[0]
        print(result)
        return {
            'language': result['language'],
            'confidence': result['confidence']
        }
