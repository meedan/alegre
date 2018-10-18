import unittest

from app.main import db
import json
from app.test.base import BaseTestCase


class TestLangidBlueprint(BaseTestCase):
    def test_langid(self):
        with self.client:
            response = self.client.post(
                '/langid/',
                data=json.dumps(dict(
                    text='Hello this is a test'
                )),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['language'] == 'en')
            self.assertTrue(data['confidence'] == -75.6393435001)
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 200)



if __name__ == '__main__':
    unittest.main()
