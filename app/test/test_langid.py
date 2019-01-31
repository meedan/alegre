import unittest
import json
import math
from google.cloud import translate

from app.main import db
from app.test.base import BaseTestCase

class TestLangidBlueprint(BaseTestCase):
    def test_langid(self):
        client = translate.Client.from_service_account_json('./google_credentials.json')
        result = client.detect_language([
            'नमस्ते मेरा नाम करीम है',
            'namaste mera naam kareem hai',
            'हॅलो माझे नाव करीम आहे',
            'হ্যালো আমার নাম কারিম',
            'હેલો, મારું નામ કરીમ છે',
            'ഹലോ എന്റെ പേര് കരീം ആണ്',
            'வணக்கம் என் பெயர் கரிம்',
            'హలో నా పేరు కరీం'
        ])
        self.assertEqual('hi', result[0]['language'])
        self.assertEqual('hi', result[1]['language'])
        self.assertEqual('mr', result[2]['language'])
        self.assertEqual('bn', result[3]['language'])
        self.assertEqual('gu', result[4]['language'])
        self.assertEqual('ml', result[5]['language'])
        self.assertEqual('ta', result[6]['language'])
        self.assertEqual('te', result[7]['language'])

    def test_langid_api(self):
        with self.client:
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


if __name__ == '__main__':
    unittest.main()
