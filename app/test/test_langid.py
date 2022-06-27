import unittest
import json
import math
import redis
import os
from flask import current_app as app
from unittest.mock import patch

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.langid import GoogleLangidProvider, MicrosoftLangidProvider, Cld3LangidProvider
from app.main.controller.langid_controller import LangidResource

class TestLangidBlueprint(BaseTestCase):
    TESTS = [
        { 'cld3': 'hi', 'microsoft': 'hi', 'google': 'hi', 'text': 'नमस्ते मेरा नाम करीम है' },
        { 'cld3': 'hi-Latn', 'microsoft': 'en', 'google': 'hi', 'text': 'namaste mera naam Karim hai' },
        { 'cld3': 'mr', 'microsoft': 'hi', 'google': 'mr', 'text': 'हॅलो माझे नाव करीम आहे' },
        { 'cld3': 'bn', 'microsoft': 'bn', 'google': 'bn', 'text': 'হ্যালো আমার নাম কারিম' },
        { 'cld3': 'hi-Latn', 'microsoft': 'id', 'google': 'bn', 'text': 'hyalo amara nama Karim' },
        { 'cld3': 'gu', 'microsoft': 'gu', 'google': 'gu', 'text': 'હેલો, મારું નામ કરીમ છે' },
        { 'cld3': 'ja-Latn', 'microsoft': 'ms', 'google': 'gu', 'text': 'helo, marum nama Karim che' },
        { 'cld3': 'ml', 'microsoft': 'ml', 'google': 'ml', 'text': 'ഹലോ എന്റെ പേര് കരീം ആണ്' },
        { 'cld3': 'ta', 'microsoft': 'ta', 'google': 'ta', 'text': 'வணக்கம் என் பெயர் கரிம்' },
        { 'cld3': 'id', 'microsoft': 'fr', 'google': 'ta', 'text': 'vanakkam en peyar Karim' },
        { 'cld3': 'te', 'microsoft': 'te', 'google': 'te', 'text': 'హలో నా పేరు కరీం' },
        { 'cld3': 'fil', 'microsoft': 'tl', 'google': 'tl', 'text': 'kamusta ang aking pangalan ay Karim' },
        { 'cld3': 'ja', 'microsoft': 'und', 'google': 'und', 'text': '🙋🏽👨‍🎤' }
    ]

    def setUp(self):
        super().setUp()
        r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
        for key in r.scan_iter("langid:*"):
            r.delete(key)

    def test_cleanup_input(self):
        STRINGS = [
            { 'text': 'this is a clean string', 'clean': 'this is a clean string' },
            { 'text': 'http://twitter.com/これは日本語です。example.com中国語', 'clean': 'これは日本語です。中国語' },
            { 'text': 'some emojis 🙋🏽👨‍🎤 for you', 'clean': 'some emojis  for you' }
        ]
        for test in STRINGS:
            self.assertEqual(test['clean'], LangidResource.cleanup_input(test['text']))

    def test_cleanup_result(self):
        RESULTS = [
            { 'test': { 'result': { 'language': 'tl', 'confidence': 1.0 }}, 'expected': { 'result': { 'language': 'fil', 'confidence': 1.0 }}},
            { 'test': { 'result': { 'language': 'hi-Latn', 'confidence': 1.0 }}, 'expected': { 'result': { 'language': 'hi', 'confidence': 1.0 }}}
        ]
        for test in RESULTS:
            self.assertEqual(test['expected'], LangidResource.cleanup_result(test['test']))

    @unittest.skipIf(os.path.isfile('../../google_credentials.json'), "Google credentials file is missing")
    def test_langid_google(self):
        for test in TestLangidBlueprint.TESTS:
            result = GoogleLangidProvider.langid(test['text'])
            self.assertEqual(test['google'], result['result']['language'], test['text'])

    # @unittest.skipIf(not app.config['MS_TEXT_ANALYTICS_KEY'], "Cognitive Services API key is missing")
    # def test_langid_microsoft(self):
    #     for test in TestLangidBlueprint.TESTS:
    #         result = MicrosoftLangidProvider.langid(test['text'])
    #         self.assertEqual(test['microsoft'], result['result']['language'], test['text'])
    #
    # def test_langid_microsoft_with_wrong_key(self):
    #     with app.app_context():
    #         app.config['MS_TEXT_ANALYTICS_KEY']='wrong_key'
    #         with self.assertRaises(Exception):
    #             MicrosoftLangidProvider.langid('hello')
    #
    def test_langid_cld3(self):
        for test in TestLangidBlueprint.TESTS:
            result = Cld3LangidProvider.langid(test['text'])
            self.assertEqual(test['cld3'], result['result']['language'], test['text'])

    def test_langid_api_get(self):
        response = self.client.get(
            '/text/langid/',
            data=json.dumps(dict(
                text='Hello this is a test'
            )),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual('en', result['result']['language'])
        self.assertEqual(app.config['PROVIDER_LANGID'], result['provider'])
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_code)

    def test_langid_api_get_with_query_request(self):
        response = self.client.get(
            '/text/langid/?text=Hello',
        )
        result = json.loads(response.data.decode())
        self.assertEqual('en', result['result']['language'])
        self.assertEqual(app.config['PROVIDER_LANGID'], result['provider'])
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_code)

    def test_langid_api_get_without_text(self):
        response = self.client.get(
            '/text/langid/',
            data=json.dumps(dict(
                text=''
            )),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual('und', result['result']['language'])
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_code)

    def test_langid_api_post(self):
        response = self.client.post(
            '/text/langid/',
            data=json.dumps(dict(
                text='Hello this is a test'
            )),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual('en', result['result']['language'])
        self.assertEqual(app.config['PROVIDER_LANGID'], result['provider'])
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
                    text='Hello this is a test',
                    provider='provider1'
                )),
                content_type='application/json'
            )
            response = self.client.get(
                '/text/langid/',
                data=json.dumps(dict(
                    text='Hello this is a test',
                    provider='provider1'
                )),
                content_type='application/json'
            )
            response = self.client.get(
                '/text/langid/',
                data=json.dumps(dict(
                    text='Hello this is a test',
                    provider='provider2'
                )),
                content_type='application/json'
            )
            self.assertEqual(mock_langid.call_count, 2)

    def test_langid_error(self):
        with patch.dict(app.config, { 'PROVIDER_LANGID': 'google' }):
            with patch('app.main.lib.langid.GoogleLangidProvider.langid', ) as mock_langid:
                mock_langid.side_effect = Exception("Simulated langid error")
                response = self.client.get(
                    '/text/langid/',
                    data=json.dumps(dict(
                        text='Hello this is a test'
                    )),
                    content_type='application/json'
                )
                result = json.loads(response.data.decode())
                self.assertEqual('application/json', response.content_type)
                self.assertEqual(500, response.status_code)

if __name__ == '__main__':
    unittest.main()
