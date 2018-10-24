import unittest
import langid
import json
import math

from app.main import db
from app.test.base import BaseTestCase

class TestLangidBlueprint(BaseTestCase):
    def test_langid(self):
        result = langid.classify('Hello this is a test')
        self.assertEqual('en', result[0])
        self.assertTrue(math.isclose(-75.6393435, result[1]))

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
            self.assertTrue(math.isclose(-75.6393435, data['confidence']))
            self.assertEqual('application/json', response.content_type)
            self.assertEqual(200, response.status_code)


if __name__ == '__main__':
    unittest.main()
