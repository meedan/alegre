import unittest

from app.main import db
import json
from app.test.base import BaseTestCase

class TestSpacyBlueprint(BaseTestCase):
    maxDiff = None

    def test_spacy(self):
        with self.client:
            response = self.client.post(
                '/spacy/',
                data=json.dumps(dict(
                    text='Pastafarians are smarter than people with Coca Cola bottles.',
                    model='en'
                )),
                content_type='application/json'
            )
            self.assertEqual('application/json', response.content_type)
            self.assertEqual(200, response.status_code)
            data = json.loads(response.data.decode())
            self.assertDictEqual(json.load(open('./app/test/data/spacy.json')), data)


if __name__ == '__main__':
    unittest.main()
