import unittest
import json
import os
from unittest.mock import patch
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account

from app.main import db
from app.main.lib.google_client import get_credentialed_google_client
from app.test.base import BaseTestCase

class TestTranslationBlueprint(BaseTestCase):
    def test_translation(self):
        client = get_credentialed_google_client(translate.Client)
        result = client.detect_language(['Me llamo', 'I am'])
        self.assertEqual('es', result[0]['language'])
        self.assertEqual('en', result[1]['language'])
        result = client.translate('koszula')
        self.assertEqual('shirt', result['translatedText'])
        self.assertEqual('pl', result['detectedSourceLanguage'])
        result = client.translate('camisa', source_language='es')
        self.assertEqual('shirt', result['translatedText'])

    def test_translation_api(self):
        with self.client:
            response = self.client.get(
                '/text/translation/',
                data=json.dumps({
                  'text': 'borracha en la oficina',
                  'from': 'es',
                  'to': 'en'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual('drunk in the office', result['text'])

            response = self.client.get(
                '/text/translation/',
                data=json.dumps({
                  'text': 'borracha na oficina',
                  'from': 'pt',
                  'to': 'en'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual('rubber in the workshop', result['text'])

            response = self.client.get(
                '/text/translation/',
                data=json.dumps({
                  'text': 'i am testing this',
                  'to': 'pt'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual('estou testando isso', result['text'].lower())

            response = self.client.get(
              '/text/translation/?text=borracha na oficina&from=pt&to=en',
            )
            result = json.loads(response.data.decode())
            self.assertEqual('rubber in the workshop', result['text'])

    def test_translation_error_if_not_credentials(self):
      with patch('os.path.exists') as mock:
        mock.return_value = {}
        with self.assertRaises(Exception):
        client = get_credentialed_google_client(translate.Client)
        self.assertEqual(None, client)
        with self.assertRaises(Exception):
          result = client.detect_language(['Me llamo', 'I am'])

if __name__ == '__main__':
    unittest.main()
