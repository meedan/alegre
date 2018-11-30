import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app

from app.main import db
from app.test.base import BaseTestCase

class TestSimilaryBlueprint(BaseTestCase):
    maxDiff = None

    def setUp(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY'])
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

    def test_similarity_queries(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      success, _ = helpers.bulk(es,
        json.load(open('./app/test/data/similarity.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      self.assertTrue(success)
      es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
      result = es.search(
        doc_type='_doc',
        index=app.config['ELASTICSEARCH_SIMILARITY'],
        body={ 'query': { 'more_like_this': { 'fields': ['text'], 'like': 'this is a test', 'min_doc_freq': 1, 'min_term_freq': 1, 'max_query_terms': 12 } } },
      )
      self.assertEqual(3, len(result['hits']['hits']))

    def test_similarity_api(self):
        with self.client:
            for term in json.load(open('./app/test/data/similarity.json')):
                del term['_type']
                response = self.client.post('/similarity/', data=json.dumps(term), content_type='application/json')
                result = json.loads(response.data.decode())
                self.assertEqual(True, result['success'])

            response = self.client.post(
                '/similarity/query',
                data=json.dumps({
                  "text": "this is a test"
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(3, len(result['result']))

            response = self.client.post(
                '/similarity/query',
                data=json.dumps({
                  "text": "something different"
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            response = self.client.post(
                '/similarity/query',
                data=json.dumps({
                  "text": "this is a test",
                  "context": {
                    "dbid": 12
                  }
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

if __name__ == '__main__':
    unittest.main()
