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
            response = self.client.get(
                '/image/ocr/',
                data=json.dumps({
                  'url': 'https://i.imgur.com/ewGClFQ.png',
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())

            self.assertIn('Translate this sentence', result['text'])
            self.assertIn('عندي وقت في الساعة العاشرة', result['text'])

    def test_ocr_api_successful_get_with_query_request(self):
        with self.client:
            response = self.client.get(
                '/image/ocr/?url=https://i.imgur.com/ewGClFQ.png',
            )
            result = json.loads(response.data.decode())

            self.assertIn('Translate this sentence', result['text'])
            self.assertIn('عندي وقت في الساعة العاشرة', result['text'])

    def test_ocr_api_image_without_text(self):
        with self.client:
            response = self.client.get(
                '/image/ocr/',
                data=json.dumps({
                  'url': 'https://i.imgur.com/LgnKoPh.png',
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertIsNone(result)

    def test_ocr_google_api_error(self):
        with patch('app.main.controller.image_ocr_controller.CLIENT') as client:
            client.return_value= Exception('We can not access the URL currently. Please download the content and pass it in')
            response = self.client.get(
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
