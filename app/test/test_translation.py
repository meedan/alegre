import unittest
from google.cloud import translate

from app.main import db
from app.test.base import BaseTestCase

class TestTranslationBlueprint(BaseTestCase):
    def test_translation(self):
        client = translate.Client.from_service_account_json('./google_credentials.json')
        result = client.detect_language(['Me llamo', 'I am'])
        self.assertEqual('es', result[0]['language'])
        self.assertEqual('en', result[1]['language'])
        result = client.translate('koszula')
        self.assertEqual('shirt', result['translatedText'])
        self.assertEqual('pl', result['detectedSourceLanguage'])
        result = client.translate('camisa', source_language='es')
        self.assertEqual('shirt', result['translatedText'])


if __name__ == '__main__':
    unittest.main()
