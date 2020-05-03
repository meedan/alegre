from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
import redis
import hashlib
import json
import importlib
import tenacity
from twitter_text import extract_urls_with_indices, extract_emojis_with_indices

api = Namespace('langid', description='langid operations')
langid_request = api.model('langid_request', {
    'text': fields.String(required=True, description='text to identify'),
    'provider': fields.String(required=False, description='langid provider to use')
})

def _after_log(retry_state):
    app.logger.debug("Retrying langid...")

@api.route('/')
class LangidResource(Resource):
    @api.response(200, 'langid successfully queried.')
    @api.doc('Identify the language of a text document')
    @api.expect(langid_request, validate=True)
    def get(self):
        provider = app.config['PROVIDER_LANGID']
        if 'provider' in request.json:
            provider = request.json['provider']

        # Read from cache first.
        r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
        key = 'langid:' + provider + ':' + hashlib.md5(request.json['text'].encode('utf-8')).hexdigest()
        try:
            result = json.loads(r.get(key))
        except:
            result = None

        # Otherwise, call the service and cache the result.
        if result == None:
            result = self.langid(LangidResource.cleanup_input(request.json['text']), provider)
            r.set(key, json.dumps(result))

        return result

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=0, max=4), stop=tenacity.stop_after_delay(10), after=_after_log)
    def langid(self, text, provider):
        if not text:
            return {
                'result': {
                    'language': 'und',
                    'confidence': 1.0
                },
                'raw': {}
            }

        # In module `app.main.lib.langid`,
        # look for a class called `#{ProviderName}LangidProvider`, e.g. `GoogleLangidProvider`
        # then call static method `langid()` on that class.
        class_ = getattr(importlib.import_module('app.main.lib.langid'), provider.title() + 'LangidProvider')

        # Cleanup the result, then add the provider information.
        return dict(LangidResource.cleanup_result(class_.langid(text)), **{ 'provider': provider })

    @staticmethod
    def cleanup_result(result):
        clean = result
        language = clean['result']['language']

        # TODO Return 'und' if confidence is low.

        # Remove region codes.
        language = language.split('-', 1)[0]

        # Special case: Convert Tagalog to Filipino.
        if language == 'tl':
            language = 'fil'

        clean['result']['language'] = language
        return clean

    @staticmethod
    def cleanup_input(text):
        clean = text
        clean = LangidResource.slice_around(clean, extract_urls_with_indices(clean))
        clean = LangidResource.slice_around(clean, extract_emojis_with_indices(clean))
        return clean.strip()

    @staticmethod
    def slice_around(text, ranges):
        # We want the text surrounding the given ranges, so we:
        # - Create surrounding ranges
        # - Create text slice for each range (end of range n -> start of range n+1)
        # - Join slices into a full string
        slices = [{'indices': [0, 0]}] + ranges + [{'indices': [len(text), len(text)]}]
        return "".join([text[s['indices'][1] : slices[i+1]['indices'][0] ] for i, s in enumerate(slices[:-1])])
