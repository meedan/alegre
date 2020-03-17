import unittest
import json
import os
import redis

from flask import current_app as app
from unittest.mock import patch
from google.cloud import vision

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.image_classification import GoogleImageClassificationProvider

class TestImageClassificationBlueprint(BaseTestCase):
    def setUp(self):
        r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
        r.flushall()

    @unittest.skipIf(os.path.isfile('../../google_credentials.json'), "Google credentials file is missing")
    def test_image_classification_google(self):
        result = GoogleImageClassificationProvider.classify('https://upload.wikimedia.org/wikipedia/en/7/7d/Lenna_%28test_image%29.png')
        self.assertDictEqual({
            'adult': vision.enums.Likelihood.VERY_UNLIKELY,
            'spoof': vision.enums.Likelihood.VERY_UNLIKELY,
            'medical': vision.enums.Likelihood.UNLIKELY,
            'violence': vision.enums.Likelihood.VERY_UNLIKELY,
            'racy': vision.enums.Likelihood.POSSIBLE,
            'spam': vision.enums.Likelihood.UNKNOWN
        }, result['result']['flags'])

    def test_image_classification_api(self):
        response = self.client.get(
            '/image/classification/',
            data=json.dumps(dict(
                uri='https://upload.wikimedia.org/wikipedia/en/7/7d/Lenna_%28test_image%29.png'
            )),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_code)
        self.assertDictEqual({
            'adult': vision.enums.Likelihood.VERY_UNLIKELY,
            'spoof': vision.enums.Likelihood.VERY_UNLIKELY,
            'medical': vision.enums.Likelihood.UNLIKELY,
            'violence': vision.enums.Likelihood.VERY_UNLIKELY,
            'racy': vision.enums.Likelihood.POSSIBLE,
            'spam': vision.enums.Likelihood.UNKNOWN
        }, result['result']['flags'])

    def test_image_classification_cache(self):
        with patch('app.main.controller.image_classification_controller.ImageClassificationResource.classify', ) as mock_image_classification:
            mock_image_classification.return_value = {
                'result': { 'flags': {
                    'adult': vision.enums.Likelihood.VERY_UNLIKELY,
                    'spoof': vision.enums.Likelihood.VERY_UNLIKELY,
                    'medical': vision.enums.Likelihood.UNLIKELY,
                    'violence': vision.enums.Likelihood.VERY_UNLIKELY,
                    'racy': vision.enums.Likelihood.POSSIBLE,
                    'spam': vision.enums.Likelihood.UNKNOWN
                }}
            }
            response = self.client.get(
                '/image/classification/',
                data=json.dumps(dict(
                    uri='https://upload.wikimedia.org/wikipedia/en/7/7d/Lenna_%28test_image%29.png'
                )),
                content_type='application/json'
            )
            response = self.client.get(
                '/text/langid/',
                data=json.dumps(dict(
                    uri='https://upload.wikimedia.org/wikipedia/en/7/7d/Lenna_%28test_image%29.png'
                )),
                content_type='application/json'
            )
            self.assertEqual(mock_image_classification.call_count, 1)

if __name__ == '__main__':
    unittest.main()
