import unittest
from unittest.mock import MagicMock
import json
from unittest.mock import patch
from collections import namedtuple
from opensearchpy import helpers, OpenSearch, TransportError
from flask import current_app as app
import numpy as np

from app.main import db
from app.test.base import BaseTestCase
from app.test.test_shared_model import SharedModelStub
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.controller import bulk_update_similarity_controller
from app.main.lib import redis_client
class TestBulkUpdateSimilarityBlueprint(BaseTestCase):
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
      r = redis_client.get_client()
      r.delete(SharedModelStub.model_key)
      r.delete('SharedModel:%s' % SharedModelStub.model_key)
      r.srem('SharedModel', SharedModelStub.model_key)

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
          with patch('importlib.import_module', ) as mock_import:
            with patch('app.main.lib.shared_models.shared_model.SharedModel.get_client', ) as mock_get_shared_model_client:
              with patch('app.main.lib.shared_models.shared_model.SharedModel.get_shared_model_response', ) as mock_get_shared_model_response:
                mock_get_shared_model_client.return_value = SharedModelStub(TestBulkUpdateSimilarityBlueprint.test_model_key)
                mock_get_shared_model_response.return_value = [0.0]
                term = { 'text': 'how to slice a banana', 'model': 'multi-sbert', 'context': { 'dbid': 54 }, 'doc_id': "123456" }
                response = self.client.post('/text/bulk_update_similarity/', data=json.dumps({"documents": [term]}), content_type='application/json')
                result = json.loads(response.data.decode())
                print(result)
                self.assertTrue(result)
                self.assertTrue(result[0]['_id'], "123456")

    def test_get_documents_by_ids(self):
        es = MagicMock()
        es.search.return_value = {
            'hits': {
                'hits': [
                    {'_id': '1', '_source': 'Document 1'},
                    {'_id': '2', '_source': 'Document 2'}
                ]
            }
        }
        index = 'test-index'
        ids = ['1', '2']
        result = bulk_update_similarity_controller.get_documents_by_ids(index, ids, es)
        expected = {'1': {'_id': '1', '_source': 'Document 1'}, '2': {'_id': '2', '_source': 'Document 2'}}
        self.assertEqual(result, expected)

    def test_merge_key_list(self):
        existing = ['a', 'b']
        new_values = ['b', 'c', 'd']
        result = bulk_update_similarity_controller.merge_key_list(existing, new_values)
        expected = ['a', 'b', 'c', 'd']
        self.assertEqual(result, expected)

    def test_get_merged_contexts(self):
        tmp_doc = {"contexts": [{"a": 1}]}
        existing_doc = {"contexts": [{"a": 1}, {"b": 2}]}
        result = bulk_update_similarity_controller.get_merged_contexts(tmp_doc, existing_doc)
        expected = [{"a": 1}, {"b": 2}]
        self.assertEqual(result, expected)

    def test_update_existing_doc_values(self):
        document = {"models": ["model_1"], "context": {"a": 1}}
        existing_doc = {"contexts": [{"a": 1}]}
        with patch('importlib.import_module', ) as mock_import:
            with patch('app.main.lib.shared_models.shared_model.SharedModel.get_client', ) as mock_get_shared_model_client:
                with patch('app.main.lib.shared_models.shared_model.SharedModel.get_shared_model_response', ) as mock_get_shared_model_response:
                    mock_get_shared_model_client.return_value = SharedModelStub(TestBulkUpdateSimilarityBlueprint.test_model_key)
                    mock_get_shared_model_response.return_value = [0.0]
                    result = bulk_update_similarity_controller.update_existing_doc_values(document, existing_doc)
                    self.assertEqual(result['contexts'], [{'a': 1}])
                    self.assertEqual(result['language'], None)
                    self.assertEqual(result['content'], None)
                    self.assertEqual(result['context'], {'a': 1})
                    self.assertEqual(result['model_model_1'], 1)
                    self.assertEqual(result['vector_model_1'], [0.0])
                    self.assertEqual(result['model'], 'model_1')

    def test_sorted_values(self):
        cases = {'1': {'a': 1}, '2': {'b': 2}}
        result_doc_ids, result_values = bulk_update_similarity_controller.sorted_values(cases)
        expected_doc_ids = ['1', '2']
        expected_values = [{'a': 1}, {'b': 2}]
        self.assertEqual(result_doc_ids, expected_doc_ids)
        self.assertEqual(result_values, expected_values)

    def test_can_add_to_bodies(self):
        existing_doc = {"contexts": [{"a": 1}]}
        updateable = True
        result = bulk_update_similarity_controller.can_add_to_bodies(existing_doc, updateable)
        self.assertTrue(result)

    def test_get_cases(self):
        params = {"documents": [{"doc_id": "1", "context": {"a": 1}}, {"doc_id": "2", "context": {"b": 1}}]}
        existing_docs = {"1": {"_source": {"contexts": [{"a": 1}]}}}
        updateable = True
        response = bulk_update_similarity_controller.get_cases(params, existing_docs, updateable)
        self.assertEqual(response[0], ['1'])
        self.assertEqual(response[1][0]['contexts'], [{'a': 1}])
        self.assertEqual(response[1][0]['language'], None)
        self.assertEqual(response[1][0]['content'], None)
        self.assertEqual(response[1][0]['context'], {'a': 1})
        self.assertEqual(response[1][0]['model_elasticsearch'], 1)

    def test_get_documents_by_ids_no_documents(self):
        es = MagicMock()
        es.search.return_value = {'hits': {'hits': []}}
        index = 'test-index'
        ids = []
        result = bulk_update_similarity_controller.get_documents_by_ids(index, ids, es)
        expected = {}
        self.assertEqual(result, expected)

    def test_merge_key_list_no_existing(self):
        existing = None
        new_values = ['a', 'b', 'c']
        result = bulk_update_similarity_controller.merge_key_list(existing, new_values)
        expected = ['a', 'b', 'c']
        self.assertEqual(result, expected)

    def test_merge_key_list_no_new_values(self):
        existing = ['a', 'b', 'c']
        new_values = []
        result = bulk_update_similarity_controller.merge_key_list(existing, new_values)
        expected = ['a', 'b', 'c']
        self.assertEqual(result, expected)

    def test_can_add_to_bodies_not_updateable(self):
        existing_doc = {"contexts": [{"a": 1}]}
        updateable = False
        result = bulk_update_similarity_controller.can_add_to_bodies(existing_doc, updateable)
        self.assertFalse(result)

    def test_can_add_to_bodies_not_updateable_no_existing_doc(self):
        existing_doc = None
        updateable = False
        result = bulk_update_similarity_controller.can_add_to_bodies(existing_doc, updateable)
        self.assertTrue(result)

    def test_get_cases_no_documents(self):
        params = {"documents": []}
        existing_docs = {"1": {"_source": {"contexts": [{"a": 1}]}}}
        updateable = True
        result_doc_ids, result_values = bulk_update_similarity_controller.get_cases(params, existing_docs, updateable)
        expected_doc_ids = []
        expected_values = []
        self.assertEqual(result_doc_ids, expected_doc_ids)
        self.assertEqual(result_values, expected_values)

    def test_get_cases_not_updateable(self):
        params = {"documents": [{"doc_id": "1", "context": {"a": 1}}, {"doc_id": "2", "context": {"a": 1}}]}
        existing_docs = {"1": {"_source": {"contexts": [{"a": 1}]}}}
        updateable = False
        response = bulk_update_similarity_controller.get_cases(params, existing_docs, updateable)
        self.assertEqual(response[0], ['2'])
        self.assertEqual(response[1][0]['contexts'], [{'a': 1}])
        self.assertEqual(response[1][0]['language'], None)
        self.assertEqual(response[1][0]['content'], None)
        self.assertEqual(response[1][0]['context'], {'a': 1})
        self.assertEqual(response[1][0]['model_elasticsearch'], 1)

if __name__ == '__main__':
    unittest.main()
