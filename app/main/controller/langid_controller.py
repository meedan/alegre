from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
import redis
import hashlib
import json
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
        # Read from cache first.
        r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
        key = 'langid:' + hashlib.md5(request.json['text'].encode('utf-8')).hexdigest()
        try:
            result = json.loads(r.get(key))
        except:
            result = None

        # Otherwise, call the service and cache the result.
        if result == None:
            result = self.langid(request.json['text'])

            # Special case: Convert Tagalog to Filipino.
            if result['language'] == 'tl':
                result['language'] = 'fil'

            r.set(key, json.dumps(result))

        return {
            'language': result['language'],
            'confidence': result['confidence']
        }

    def langid(self, text):
        client = translate.Client.from_service_account_json('./google_credentials.json')
        return client.detect_language([text])[0]
