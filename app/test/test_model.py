import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app

from app.main import db
from app.test.base import BaseTestCase

class TestModelBlueprint(BaseTestCase):
    def test_model_api(self):
        with self.client:
            response = self.client.get('/model/')
            result = json.loads(response.data.decode())
            self.assertListEqual(sorted([
              'universal-sentence-encoder-large',
              'wordvec-glove-6B-50d'
            ]), sorted(result['models']))