from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from google.cloud import translate_v2 as translate

from app.main.lib.google_client import get_credentialed_google_client

api = Namespace('translation', description='machine translation operations')
translation_request = api.model('translation_request', {
    'text': fields.String(required=True, description='text to be translated'),
    'from': fields.String(required=False, description='source language'),
    'to': fields.String(required=True, description='target language'),
})

@api.route('/')
class TranslationResource(Resource):
    @api.response(200, 'text successfully translated.')
    @api.doc('Machine-translate a text document')
    @api.expect(translation_request, validate=True)
    def get(self):
        client = get_credentialed_google_client(translate.Client)
        source_language = None
        if 'from' in request.json:
            source_language = request.json['from']
        else:
            source_language = client.detect_language([request.json['text']])[0]['language']
        result = client.translate(request.json['text'], source_language=source_language, target_language=request.json['to'])
        return {
            'text': result['translatedText']
        }
