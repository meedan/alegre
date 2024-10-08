import unittest
import json
import os

from flask import current_app as app
from unittest.mock import patch
from google.cloud import vision

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.image_classification import GoogleImageClassificationProvider
from app.main.lib import redis_client

class TestImageClassificationBlueprint(BaseTestCase):
    def setUp(self):
        super().setUp()
        r = redis_client.get_client()
        for key in r.scan_iter("image_classification:*"):
            r.delete(key)

    def test_image_classification_api(self):
        response = self.client.post(
            '/image/classification/',
            data=json.dumps(dict(
                uri='https://i.pinimg.com/564x/5f/35/b1/5f35b1bce78a5e51c4f356ddbacf840f.jpg'
            )),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(app.config['PROVIDER_IMAGE_CLASSIFICATION'], result['provider'])
        self.assertEqual(200, response.status_code)
        self.assertDictEqual({
            'adult': vision.enums.Likelihood.VERY_UNLIKELY,
            'medical': vision.enums.Likelihood.UNLIKELY,
            'racy': vision.enums.Likelihood.VERY_UNLIKELY,
            'spam': vision.enums.Likelihood.UNKNOWN,
            'spoof': vision.enums.Likelihood.POSSIBLE,
            'violence': vision.enums.Likelihood.UNLIKELY
        }, result['result']['flags'])

    def test_image_classification_api_with_query_request(self):
        response = self.client.post(
            '/image/classification/',
            data=json.dumps({"uri":"https://i.pinimg.com/564x/5f/35/b1/5f35b1bce78a5e51c4f356ddbacf840f.jpg"}),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(app.config['PROVIDER_IMAGE_CLASSIFICATION'], result['provider'])
        self.assertEqual(200, response.status_code)
        self.assertDictEqual({
            'adult': vision.enums.Likelihood.VERY_UNLIKELY,
            'medical': vision.enums.Likelihood.UNLIKELY,
            'racy': vision.enums.Likelihood.VERY_UNLIKELY,
            'spam': vision.enums.Likelihood.UNKNOWN,
            'spoof': vision.enums.Likelihood.POSSIBLE,
            'violence': vision.enums.Likelihood.UNLIKELY
        }, result['result']['flags'])

    def test_image_classification_error(self):
        response = self.client.post(
            '/image/classification/',
            data=json.dumps(dict(
                uri='https://bad.url/blah'
            )),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(500, response.status_code)

    def test_image_classification_cache(self):
        with patch('app.main.controller.image_classification_controller.ImageClassificationResource.classify', ) as mock_image_classification:
            mock_image_classification.return_value = {
                'result': { 'flags': {
                    'adult': vision.enums.Likelihood.VERY_UNLIKELY,
                    'spoof': vision.enums.Likelihood.VERY_UNLIKELY,
                    'medical': vision.enums.Likelihood.UNLIKELY,
                    'violence': vision.enums.Likelihood.VERY_UNLIKELY,
                    'racy': vision.enums.Likelihood.VERY_UNLIKELY,
                    'spam': vision.enums.Likelihood.UNKNOWN
                }}
            }
            response = self.client.post(
                '/image/classification/',
                data=json.dumps(dict(
                    uri='https://i.imgur.com/ewGClFQ.png'
                )),
                content_type='application/json'
            )
            response = self.client.post(
                '/image/classification/',
                data=json.dumps(dict(
                    uri='https://i.imgur.com/ewGClFQ.png'
                )),
                content_type='application/json'
            )
            self.assertEqual(mock_image_classification.call_count, 1)

    def test_image_classification_google_raise_error(self):
        with patch('app.main.lib.image_classification.CLIENT', None):
            with self.assertRaises(Exception):
                GoogleImageClassificationProvider.classify('https://i.imgur.com/ewGClFQ.png')

if __name__ == '__main__':
    unittest.main()