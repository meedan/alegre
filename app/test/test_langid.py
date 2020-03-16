import unittest
import json
import math
import redis
import os
from flask import current_app as app
from unittest.mock import patch

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.langid import GoogleLangidProvider, MicrosoftLangidProvider

class TestLangidBlueprint(BaseTestCase):
    TESTS = [
        { 'microsoft': 'hi', 'google': 'hi', 'text': 'नमस्ते मेरा नाम करीम है' },
        { 'microsoft': 'en', 'google': 'hi', 'text': 'namaste mera naam Karim hai' },
        { 'microsoft': 'hi', 'google': 'mr', 'text': 'हॅलो माझे नाव करीम आहे' },
        { 'microsoft': 'bn', 'google': 'bn', 'text': 'হ্যালো আমার নাম কারিম' },
        { 'microsoft': 'id', 'google': 'bn', 'text': 'hyalo amara nama Karim' },
        { 'microsoft': 'gu', 'google': 'gu', 'text': 'હેલો, મારું નામ કરીમ છે' },
        { 'microsoft': 'en', 'google': 'gu', 'text': 'helo, marum nama Karim che' },
        { 'microsoft': 'ml', 'google': 'ml', 'text': 'ഹലോ എന്റെ പേര് കരീം ആണ്' },
        { 'microsoft': 'ta', 'google': 'ta', 'text': 'வணக்கம் என் பெயர் கரிம்' },
        { 'microsoft': 'fr', 'google': 'ta', 'text': 'vanakkam en peyar Karim' },
        { 'microsoft': 'te', 'google': 'te', 'text': 'హలో నా పేరు కరీం' },
        { 'microsoft': 'tl', 'google': 'tl', 'text': 'kamusta ang aking pangalan ay Karim' }
    ]

    def setUp(self):
        r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
        r.flushall()

    @unittest.skipIf(os.path.isfile('../../google_credentials.json'), "Google credentials file is missing")
    def test_langid_google(self):
        for test in TestLangidBlueprint.TESTS:
            result = GoogleLangidProvider.langid(test['text'])
            self.assertEqual(test['google'], result['result']['language'], test['text'])

    @unittest.skipIf(not app.config['MS_TEXT_ANALYTICS_KEY'], "Cognitive Services API key is missing")
    def test_langid_microsoft(self):
        for test in TestLangidBlueprint.TESTS:
            result = MicrosoftLangidProvider.langid(test['text'])
            self.assertEqual(test['microsoft'], result['result']['language'], test['text'])

    def test_langid_api(self):
        response = self.client.get(
            '/text/langid/',
            data=json.dumps(dict(
                text='Hello this is a test'
            )),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual('en', result['result']['language'])
        self.assertTrue(math.isclose(1, result['result']['confidence']))
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_code)

    def test_langid_cache(self):
        with patch('app.main.controller.langid_controller.LangidResource.langid', ) as mock_langid:
            mock_langid.return_value = {
                'result': {
                    'language': 'en',
                    'confidence': 1.0
                }
            }
            response = self.client.get(
                '/text/langid/',
                data=json.dumps(dict(
                    text='Hello this is a test'
                )),
                content_type='application/json'
            )
            response = self.client.get(
                '/text/langid/',
                data=json.dumps(dict(
                    text='Hello this is a test'
                )),
                content_type='application/json'
            )
            self.assertEqual(mock_langid.call_count, 1)

if __name__ == '__main__':
    unittest.main()
