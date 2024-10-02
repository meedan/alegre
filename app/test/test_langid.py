import unittest
import json
import math
import os
from flask import current_app as app
from unittest.mock import patch

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.langid import GoogleLangidProvider, Cld3LangidProvider, FastTextLangidProvider, HybridLangidProvider
from app.main.controller.langid_controller import LangidResource
from app.main.lib import redis_client

class TestLangidBlueprint(BaseTestCase):
    TESTS = [
        { 'fasttext': 'hi', 'cld3': 'hi', 'microsoft': 'hi', 'google': 'hi', 'text': 'नमस्ते मेरा नाम करीम है' },
        { 'fasttext': None, 'cld3': 'hi-Latn', 'microsoft': 'en', 'google': ['hi', 'hi-Latn'], 'text': 'namaste mera naam Karim hai' },
        { 'fasttext': 'mr', 'cld3': 'mr', 'microsoft': 'hi', 'google': 'mr', 'text': 'हॅलो माझे नाव करीम आहे' },
        { 'fasttext': 'bn', 'cld3': 'bn', 'microsoft': 'bn', 'google': 'bn', 'text': 'হ্যালো আমার নাম কারিম' },
        { 'fasttext': None, 'cld3': 'hi-Latn', 'microsoft': 'id', 'google': ['bn', 'bn-Latn'], 'text': 'hyalo amara nama Karim' },
        { 'fasttext': 'gu', 'cld3': 'gu', 'microsoft': 'gu', 'google': 'gu', 'text': 'હેલો, મારું નામ કરીમ છે' },
        { 'fasttext': None, 'cld3': 'ja-Latn', 'microsoft': 'ms', 'google': ['gu', 'gu-Latn'], 'text': 'helo, marum nama Karim che' },
        { 'fasttext': 'ml', 'cld3': 'ml', 'microsoft': 'ml', 'google': 'ml', 'text': 'ഹലോ എന്റെ പേര് കരീം ആണ്' },
        { 'fasttext': 'ta', 'cld3': 'ta', 'microsoft': 'ta', 'google': 'ta', 'text': 'வணக்கம் என் பெயர் கரிம்' },
        { 'fasttext': None, 'cld3': 'id', 'microsoft': 'fr', 'google': ['ta', 'ta-Latn'], 'text': 'vanakkam en peyar Karim' },
        { 'fasttext': 'te', 'cld3': 'te', 'microsoft': 'te', 'google': 'te', 'text': 'హలో నా పేరు కరీం' },
        { 'fasttext': 'fil', 'cld3': 'fil', 'microsoft': 'tl', 'google': ['fil', 'tl', 'tl-Latn'], 'text': 'kamusta ang aking pangalan ay Karim' },
        { 'fasttext': None, 'cld3': 'ja', 'microsoft': 'und', 'google': 'und', 'text': '🙋🏽👨‍🎤' }
    ]

    def setUp(self):
        super().setUp()
        r = redis_client.get_client()
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

    # @unittest.skipIf(os.path.isfile('../../google_credentials.json'), "Google credentials file is missing")
    # def test_langid_google(self):
    #     for test in TestLangidBlueprint.TESTS:
    #         result = GoogleLangidProvider.langid(test['text'])
    #         if type(test['google']) == str:
    #             self.assertEqual(test['google'], result['result']['language'], test['text'])
    #         else:
    #             self.assertTrue(result['result']['language'] in test['google'])

    @unittest.skipIf(os.path.isfile('../../google_credentials.json'), "Google credentials file is missing")
    def test_langid_hybrid(self):
        for test in TestLangidBlueprint.TESTS:
            result = HybridLangidProvider.langid(test['text'])
            if type(test['google']) == str:
                self.assertEqual(test['google'], result['result']['language'], test['text'])
            else:
                self.assertTrue(result['result']['language'] in test['google'])

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

    def test_langid_fasttext(self):
        for test in TestLangidBlueprint.TESTS:
            if test['fasttext']!=None:
                result = FastTextLangidProvider.langid(test['text'])
                self.assertEqual(test['fasttext'], result['result']['language'], test['text'])

    def test_langid_api_get(self):
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

    def test_langid_api_get_without_text(self):
        response = self.client.post(
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
            response = self.client.post(
                '/text/langid/',
                data=json.dumps(dict(
                    text='Hello this is a test',
                    provider='provider1'
                )),
                content_type='application/json'
            )
            response = self.client.post(
                '/text/langid/',
                data=json.dumps(dict(
                    text='Hello this is a test',
                    provider='provider1'
                )),
                content_type='application/json'
            )
            response = self.client.post(
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
                response = self.client.post(
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