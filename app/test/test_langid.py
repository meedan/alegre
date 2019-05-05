import unittest
import json
import math
import redis
from google.cloud import translate
from flask import current_app as app
from unittest.mock import patch

from app.main import db
from app.test.base import BaseTestCase

class TestLangidBlueprint(BaseTestCase):
    def setUp(self):
        r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
        r.flushall()

    def test_langid(self):
        client = translate.Client.from_service_account_json('./google_credentials.json')
        result = client.detect_language([
            'नमस्ते मेरा नाम करीम है',
            'namaste mera naam kareem hai',
            'हॅलो माझे नाव करीम आहे',
            'হ্যালো আমার নাম কারিম',
            'hyalo amara nama karim',
            'હેલો, મારું નામ કરીમ છે',
            'helo, marum nama karim che',
            'ഹലോ എന്റെ പേര് കരീം ആണ്',
            'வணக்கம் என் பெயர் கரிம்',
            'vanakkam en peyar karim',
            'హలో నా పేరు కరీం'
        ])
        self.assertEqual('hi', result[0]['language'])
        self.assertEqual('hi', result[1]['language'])
        self.assertEqual('mr', result[2]['language'])
        self.assertEqual('bn', result[3]['language'])
        self.assertEqual('bn', result[4]['language'])
        self.assertEqual('gu', result[5]['language'])
        self.assertEqual('gu', result[6]['language'])
        self.assertEqual('ml', result[7]['language'])
        self.assertEqual('ta', result[8]['language'])
        self.assertEqual('ta', result[9]['language'])
        self.assertEqual('te', result[10]['language'])

    def test_langid_api(self):
        response = self.client.post(
            '/langid/',
            data=json.dumps(dict(
                text='Hello this is a test'
            )),
            content_type='application/json'
        )
        data = json.loads(response.data.decode())
        self.assertEqual('en', data['language'])
        self.assertTrue(math.isclose(1, data['confidence']))
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_code)

    def test_langid_cache(self):
        with patch('app.main.controller.langid_controller.LangidResource.langid', ) as mock_langid:
            mock_langid.return_value = {
                'language': 'en',
                'confidence': 1.0
            }
            response = self.client.post(
                '/langid/',
                data=json.dumps(dict(
                    text='Hello this is a test'
                )),
                content_type='application/json'
            )
            response = self.client.post(
                '/langid/',
                data=json.dumps(dict(
                    text='Hello this is a test'
                )),
                content_type='application/json'
            )
            self.assertEqual(mock_langid.call_count, 1)

if __name__ == '__main__':
    unittest.main()
