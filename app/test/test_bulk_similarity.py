import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app
import numpy as np

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel

class TestBulkSimilarityBlueprint(BaseTestCase):
    maxDiff = None
    use_model_key = 'multi-sbert'
    test_model_key = 'shared-model-test'

    def setUp(self):
      super().setUp()
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], ignore=[400, 404])
      es.indices.create(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_mapping(
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
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      self.assertDictEqual(
        json.load(open('./elasticsearch/alegre_similarity.json')),
        mapping[app.config['ELASTICSEARCH_SIMILARITY']]['mappings']
      )

    def test_elasticsearch_update_text(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 } }
            post_response = self.client.post('/text/bulk_similarity/', data=json.dumps({"documents": [term]}), content_type='application/json')
            es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            term2 = { 'text': 'how to slice a pizza', 'model': 'elasticsearch', 'context': { 'dbid': 54 }, 'doc_id': doc["_id"]}
            post_response2 = self.client.post('/text/bulk_similarity/', data=json.dumps({"documents": [term2]}), content_type='application/json')
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if doc["_id"] == e["_id"]][0]
            self.assertEqual(term2['text'], doc['_source']['content'])

    def test_elasticsearch_update_text_with_doc_id(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 }, 'doc_id': "123456" }
            post_response = self.client.post('/text/bulk_similarity/', data=json.dumps({"documents": [term]}), content_type='application/json')
            es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            term2 = { 'text': 'how to slice a pizza', 'model': 'elasticsearch', 'context': { 'dbid': 54 }, 'doc_id': "123456"}
            post_response2 = self.client.post('/text/bulk_similarity/', data=json.dumps({"documents": [term2]}), content_type='application/json')
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if doc["_id"] == e["_id"]][0]
            self.assertEqual(term2['text'], doc['_source']['content'])

    def test_elasticsearch_delete_text(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 } }
            post_response = self.client.post('/text/bulk_similarity/', data=json.dumps({"documents": [term]}), content_type='application/json')
            result = json.loads(post_response.data.decode())
            self.assertEqual(True, result[0]['success'])
            es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            delete_response = self.client.delete(
                '/text/bulk_similarity/',
                data=json.dumps({"documents": [{"doc_id": doc["_id"]}]}),
                content_type='application/json'
            )
            result = json.loads(delete_response.data.decode())
            self.assertEqual('deleted', result['result'])

if __name__ == '__main__':
    unittest.main()
