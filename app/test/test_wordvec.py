import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app

from app.main import db
from app.test.base import BaseTestCase

class TestWordVecBlueprint(BaseTestCase):
    def test_wordvec_api(self):
        with self.client:
            response = self.client.post(
                '/text/wordvec/vector',
                data=json.dumps({
                  "text": "this is a test",
                  "model": "WordVec",
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            vector = result['vector']

            response = self.client.post(
                '/text/wordvec/similarity',
                data=json.dumps({
                  "vector1": vector,
                  "vector2": vector,
                  "model": "WordVec",
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            similarity = result['similarity']
            self.assertEqual(1.0, similarity)

            response = self.client.post(
                '/text/wordvec/vector',
                data=json.dumps({
                  "text": "how to delete an invoice",
                  "model": "WordVec",
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            vector1 = result['vector']

            response = self.client.post(
                '/text/wordvec/vector',
                data=json.dumps({
                  "text": "purge an invoice",
                  "model": "WordVec",
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            vector2 = result['vector']

            response = self.client.post(
                '/text/wordvec/similarity',
                data=json.dumps({
                  "vector1": vector1,
                  "vector2": vector2,
                  "model": "WordVec",
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            similarity = result['similarity']
            self.assertNotEqual(1.0, similarity)
            self.assertGreater(similarity, 0.7)
