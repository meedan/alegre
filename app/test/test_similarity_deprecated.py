import unittest
import json
from opensearchpy import helpers, OpenSearch, TransportError
from flask import current_app as app
import numpy as np

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel
from unittest.mock import patch

class TestSimilarityBlueprintDeprecated(BaseTestCase):
"""
These tests involve text vectorization functionality provided by presto.  
# TODO: update to new similarity endpoints after vectorization is available in CI env: https://meedan.atlassian.net/browse/CV2-6160
"""

    maxDiff = None
    use_model_key = 'xlm-r-bert-base-nli-stsb-mean-tokens'
    test_model_key = 'indian-sbert'

    def setUp(self):
      super().setUp()
      es = OpenSearch(app.config['ELASTICSEARCH_URL'])
      es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], ignore=[400, 404])
      es.indices.create(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_mapping(
        body=json.load(open('./elasticsearch/alegre_similarity.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )

    def test_model_similarity(self):
        with self.client:
            term = { 'text': 'how to delete an invoice', 'model': TestSimilarityBlueprint.use_model_key, 'context': { 'dbid': 54 } }
            response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            result = json.loads(response.data.decode())
            self.assertEqual(True, result['success'])

        es = OpenSearch(app.config['ELASTICSEARCH_URL'])
        es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
        response = self.client.post(
            '/text/similarity/search/',
            data=json.dumps({
              'text': 'how to delete an invoice',
              'model': TestSimilarityBlueprint.use_model_key,
              'context': {
                'dbid': 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['score']
        self.assertGreater(similarity, 0.7)

        response = self.client.post(
            '/text/similarity/search/',
            data=json.dumps({
              'text': 'purge an invoice',
              'model': TestSimilarityBlueprint.use_model_key,
              'threshold': 0.7,
              'context': {
                'dbid': 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        response = self.client.post(
            '/text/similarity/search/',
            data=json.dumps({
              'text': 'purge an invoice',
              'model': TestSimilarityBlueprint.use_model_key,
              'threshold': 0.7,
              'per_model_threshold': {TestSimilarityBlueprint.use_model_key: 0.7},
              'context': {
                'dbid': 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['score']
        self.assertGreater(similarity, 0.7)

        response = self.client.post(
            '/text/similarity/search/',
            data=json.dumps({
              'text': 'purge an invoice',
              'model': TestSimilarityBlueprint.use_model_key,
              'threshold': 0.7
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['score']
        self.assertGreater(similarity, 0.7)

    def test_wrong_model_key(self):
        """
        Tests querying with a model key that doesn't match the one content was index with
        """
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': TestSimilarityBlueprint.use_model_key, 'context': { 'dbid': 54 }}
            response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            result = json.loads(response.data.decode())
            self.assertEqual(True, result['success'])

        es = OpenSearch(app.config['ELASTICSEARCH_URL'])
        es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])

        response = self.client.post(
            '/text/similarity/search/',
            data=json.dumps({
              'text': 'how to slice a banana',
              'model': TestSimilarityBlueprint.test_model_key,
              'context': {
                'dbid': 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(0, len(result['result']))

    def test_model_similarity_with_vector(self):
      with self.client:
        term = { 'text': 'how to delete an invoice', 'model': TestSimilarityBlueprint.use_model_key, 'context': { 'dbid': 54 }}
        response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(True, result['success'])

      es = OpenSearch(app.config['ELASTICSEARCH_URL'])
      es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])

      model = SharedModel.get_client(TestSimilarityBlueprint.use_model_key)
      vector = model.get_shared_model_response('how to delete an invoice')

      response = self.client.post(
          '/text/similarity/search/',
          data=json.dumps({
            'text': 'how to delete an invoice',
            'model': TestSimilarityBlueprint.use_model_key,
            'vector': vector
          }),
          content_type='application/json'
      )
      result = json.loads(response.data.decode())
      self.assertEqual(1, len(result['result']))

if __name__ == '__main__':
    unittest.main()