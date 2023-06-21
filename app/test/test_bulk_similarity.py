import unittest
import json
from opensearchpy import helpers, OpenSearch, TransportError
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
      es = OpenSearch(app.config['ELASTICSEARCH_URL'])
      es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], ignore=[400, 404])
      es.indices.create(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_mapping(
        body=json.load(open('./elasticsearch/alegre_similarity.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )

    def test_similarity_mapping(self):
      es = OpenSearch(app.config['ELASTICSEARCH_URL'])
      mapping = es.indices.get_mapping(
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      self.assertDictEqual(
        json.load(open('./elasticsearch/alegre_similarity.json')),
        mapping[app.config['ELASTICSEARCH_SIMILARITY']]['mappings']
      )

    def test_elasticsearch_insert_text_with_doc_id(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 }, 'doc_id': "123456" }
            response = self.client.post('/text/bulk_similarity/', data=json.dumps({"documents": [term]}), content_type='application/json')
            result = json.loads(response.data.decode())
            self.assertTrue(result)
            self.assertTrue(result[0]['_id'], "123456")


    def test_bulk_similarity_with_diferent_model(self):
      with self.client:
        term = { 'text': 'how to slice a banana', 'model': 'xlm-r-bert-base-nli-stsb-mean-tokens', 'context': { 'dbid': 54 }, 'doc_id': "123456" }
        response = self.client.post('/text/bulk_similarity/', data=json.dumps({"documents": [term]}), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertTrue(result)
        self.assertTrue(result[0]['_id'], "123456")

if __name__ == '__main__':
    unittest.main()
