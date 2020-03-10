from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
import redis
import hashlib
import json
import importlib

api = Namespace('langid', description='langid operations')
langid_request = api.model('langid_request', {
    'text': fields.String(required=True, description='text to identify')
})

@api.route('/')
class LangidResource(Resource):
    @api.response(200, 'langid successfully queried.')
    @api.doc('Identify the language of a text document')
    @api.expect(langid_request, validate=True)
    def get(self):
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
            'result': result
        }

    def langid(self, text):
        # In module `app.main.lib.langid`,
        # look for a class called `#{ProviderName}LangidProvider`, e.g. `GoogleLangidProvider`
        # then call static method `langid()` on that class.
        class_ = getattr(importlib.import_module('app.main.lib.langid'), app.config['PROVIDER_LANGID'].title() + 'LangidProvider')
        return class_.langid(text)
