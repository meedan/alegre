import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app
import numpy as np

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel

class TestSimilaryBlueprint(BaseTestCase):
    maxDiff = None
    use_model_key = 'multi-sbert'
    test_model_key = 'shared-model-test'

    def setUp(self):
      super().setUp()
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], ignore=[400, 404])
      es.indices.create(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_mapping(
        doc_type='_doc',
        body=json.load(open('./elasticsearch/alegre_similarity.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      es.indices.close(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_settings(
        body=json.load(open('./elasticsearch/alegre_similarity_settings.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      es.indices.open(index=app.config['ELASTICSEARCH_SIMILARITY'])

    def test_similarity_mapping(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      mapping = es.indices.get_mapping(
        doc_type='_doc',
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      self.assertDictEqual(
        json.load(open('./elasticsearch/alegre_similarity.json')),
        mapping[app.config['ELASTICSEARCH_SIMILARITY']]['mappings']['_doc']
      )

    def test_elasticsearch_similarity_english(self):
        with self.client:
            for term in json.load(open('./app/test/data/similarity.json')):
                del term['_type']
                term['text'] = term['content']
                del term['content']
                response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
                result = json.loads(response.data.decode())
                self.assertEqual(True, result['success'])

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'this is a test'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(3, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'something different'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'this is a test',
                  'context': {
                    'dbid': 12,
                    'app': 'check'
                  }
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'Magnitude 4.5 quake strikes near Fort St. John',
                  'threshold': 0.7
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(2, len(result['result']))

    def test_elasticsearch_similarity_hindi(self):
        with self.client:
            for term in [
              { 'text': 'नमस्ते मेरा नाम करीम है' },
              { 'text': 'हॅलो माझे नाव करीम आहे' }
            ]:
              response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
              result = json.loads(response.data.decode())
              self.assertEqual(True, result['success'])

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'नमस्ते मेरा नाम करीम है',
                  'language': 'en'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(2, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'नमस्ते मेरा नाम करीम है',
                  'language': 'hi'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

    def test_model_similarity(self):
        with self.client:
            term = { 'text': 'how to delete an invoice', 'model': TestSimilaryBlueprint.use_model_key, 'context': { 'dbid': 54 } }
            response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            result = json.loads(response.data.decode())
            self.assertEqual(True, result['success'])

        response = self.client.get(
            '/text/similarity/',
            data=json.dumps({
              'text': 'how to delete an invoice',
              'model': TestSimilaryBlueprint.use_model_key,
              'context': {
                'dbid': 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

        response = self.client.get(
            '/text/similarity/',
            data=json.dumps({
              'text': 'purge an invoice',
              'model': TestSimilaryBlueprint.use_model_key,
              'threshold': 0.7,
              'context': {
                'dbid': 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

        response = self.client.get(
            '/text/similarity/',
            data=json.dumps({
              'text': 'purge an invoice',
              'model': TestSimilaryBlueprint.use_model_key,
              'threshold': 0.7
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

    def test_wrong_model_key(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': TestSimilaryBlueprint.use_model_key, 'context': { 'dbid': 54 } }
            response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            result = json.loads(response.data.decode())
            self.assertEqual(True, result['success'])

        response = self.client.get(
            '/text/similarity/',
            data=json.dumps({
              'text': 'how to slice a banana',
              'model': TestSimilaryBlueprint.test_model_key,
              'context': {
                'dbid': 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(0, len(result['result']))

if __name__ == '__main__':
    unittest.main()
