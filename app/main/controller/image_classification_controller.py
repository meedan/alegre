from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
import redis
import hashlib
import json
import importlib
import tenacity

api = Namespace('image_classification', description='image classification operations')
image_classification_request = api.model('image_classification_request', {
    'uri': fields.String(required=True, description='image URL to be queried for classification')
})

def _after_log(retry_state):
    app.logger.debug("Retrying image classification...")

@api.route('/')
class ImageClassificationResource(Resource):
    @api.response(200, 'image classification successfully queried.')
    @api.doc('Classify and label an image')
    @api.expect(image_classification_request, validate=True)
    def get(self):
        # Read from cache first.
        r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
        key = 'image_classification:' + hashlib.md5(request.json['uri'].encode('utf-8')).hexdigest()
        try:
            result = json.loads(r.get(key))
        except:
            result = None

        # Otherwise, call the service and cache the result.
        if result == None:
            result = self.classify(request.json['uri'])
            r.set(key, json.dumps(result))

        return result

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=0, max=4), stop=tenacity.stop_after_delay(10), after=_after_log)
    def classify(self, uri):
        # In module `app.main.lib.image_classification`,
        # look for a class called `#{ProviderName}ImageClassificationProvider`, e.g. `GoogleImageClassificationProvider`
        # then call static method `classify()` on that class.
        class_ = getattr(importlib.import_module('app.main.lib.image_classification'), app.config['PROVIDER_IMAGE_CLASSIFICATION'].title() + 'ImageClassificationProvider')
        return dict(class_.classify(uri), **{ 'provider': app.config['PROVIDER_IMAGE_CLASSIFICATION'] })
