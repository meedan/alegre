import unittest
import json
from google.cloud import translate_v2 as translate

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
                  'text': 'I am testing this',
                  'to': 'pt'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual('estou testando isso', result['text'].lower())

if __name__ == '__main__':
    unittest.main()
