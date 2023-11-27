import unittest
import json
from google.cloud import vision
from unittest.mock import patch
from app.main import db
from app.main.lib.google_client import get_credentialed_google_client
from app.test.base import BaseTestCase
from google.cloud import vision

class TestOcrBlueprint(BaseTestCase):
    def test_ocr_api_successful(self):
        with self.client:
            response = self.client.post(
                '/image/ocr/',
                data=json.dumps({
                  'url': 'https://i.pinimg.com/564x/5f/35/b1/5f35b1bce78a5e51c4f356ddbacf840f.jpg',
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())

            self.assertIn('selected by the editor', result['text'])
            self.assertIn('The New York Times', result['text'])

    def test_ocr_api_image_without_text(self):
        with self.client:
            response = self.client.post(
                '/image/ocr/',
                data=json.dumps({
                  'url': 'https://i.pinimg.com/564x/0d/da/56/0dda56a791e3af7a4023f073b4d3c099.jpg',
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertIsNone(result)

    def test_ocr_google_api_error(self):
        with patch('app.main.controller.image_ocr_controller.CLIENT') as client:
            client.return_value= Exception('We can not access the URL currently. Please download the content and pass it in')
            response = self.client.post(
                '/image/ocr/',
                data=json.dumps({
                'url': 'https://i.imgur.com/ewGClFQ.png',
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertIn('Error', result['message'])

if __name__ == '__main__':
    unittest.main()