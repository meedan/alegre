import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app

from app.main import db
from app.test.base import BaseTestCase

class TestMultiSBERTModelBlueprint(BaseTestCase):
    use_model_key = "multi-sbert"

    def test_universal_sentence_encoder_api(self):
        with self.client:
            response = self.client.post(
                '/model/vector',
                data=json.dumps({
                  "text": "this is a test",
                  "model": TestMultiSBERTModelBlueprint.use_model_key,
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            vector = result['vector']

            response = self.client.post(
                '/model/similarity',
                data=json.dumps({
                  "vector1": vector,
                  "vector2": vector,
                  "model": TestMultiSBERTModelBlueprint.use_model_key,
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            similarity = result['similarity']
            self.assertEqual(1.0, similarity)

            response = self.client.post(
                '/model/vector',
                data=json.dumps({
                  "text": "how to delete an invoice",
                  "model": TestMultiSBERTModelBlueprint.use_model_key,
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            vector1 = result['vector']

            response = self.client.post(
                '/model/vector',
                data=json.dumps({
                  "text": "purge an invoice",
                  "model": TestMultiSBERTModelBlueprint.use_model_key,
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            vector2 = result['vector']

            response = self.client.post(
                '/model/similarity',
                data=json.dumps({
                  "vector1": vector1,
                  "vector2": vector2,
                  "model": TestMultiSBERTModelBlueprint.use_model_key,
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            similarity = result['similarity']
            self.assertNotEqual(1.0, similarity)
            self.assertGreater(similarity, 0.7)
