from unittest.mock import patch, MagicMock
from flask import current_app as app
from opensearchpy import OpenSearch, TransportError
from app.main.lib.elastic_crud import save, delete, add, get_by_doc_id_or_url, get_object
import unittest
import json


class TestElasticCrud(unittest.TestCase):
    @patch('app.main.lib.elastic_crud.OpenSearch')
    def test_save_existing_object(self, mock_opensearch):
        # Mock existing document in Elasticsearch
        mock_es = mock_opensearch.return_value
        mock_es.search.return_value = {'hits': {'hits': [{'id': '1', '_source': {'url': 'http://example.com', 'context': [{'foo': 'bar'}, {'baz': 'bat'}]}}]}}
        mock_es.index.return_value = {'result': 'updated'}

        # Calling save function with an object having the same URL
        obj = {'url': 'http://example.com', 'context': [{'foo': 'bar'}, {'baz': 'bat'}]}
        result = save(obj)

        # Check if existing object is updated in Elasticsearch
        self.assertTrue(result['result'] == 'updated')

    @patch('app.main.lib.elastic_crud.OpenSearch')
    def test_save_new_object(self, mock_opensearch):
        # Mock no existing document in Elasticsearch
        mock_es = mock_opensearch.return_value
        mock_es.search.return_value = {'hits': {'hits': []}}
        mock_es.index.return_value = {'result': 'created'}

        # Calling save function with a new object
        obj = {'url': 'http://newexample.com', 'context': 'new_context'}
        result = save(obj)

        # Check if new object is added in Elasticsearch
        self.assertTrue(result['result'] == 'created')

    @patch('app.main.lib.elastic_crud.OpenSearch')
    def test_save_exception_handling(self, mock_opensearch):
        # Mocking an exception during the save process
        mock_es = mock_opensearch.return_value
        mock_es.index.side_effect = TransportError(500, 'Internal Server Error')

        obj = {'url': 'http://exceptionexample.com', 'context': 'new_context'}

        # Expecting an exception to be raised
        with self.assertRaises(TransportError):
            save(obj)

    @patch('app.main.lib.elastic_crud.OpenSearch')
    def test_delete(self, mock_opensearch):
        # Mock existing document in Elasticsearch
        mock_es = mock_opensearch.return_value
        mock_es.search.return_value = {'hits': {'hits': [{'id': '1', '_source': {'url': 'http://example.com'}}]}}
        mock_es.delete.return_value = {'result': 'deleted'}

        # Test case: Object found and deleted
        obj = {'url': 'http://example.com'}
        result = delete(obj)

        self.assertTrue(result['result'] == 'deleted')

        # Test case: Object not found
        mock_es.search.return_value = {'hits': {'hits': []}}
        result = delete(obj)

        self.assertFalse(result['result'])

    @patch('app.main.lib.elastic_crud.OpenSearch')
    @patch('app.main.lib.elastic_crud.save')
    def test_add(self, mock_save, mock_opensearch):
        # Setup
        mock_es = mock_opensearch.return_value
        mock_es.search.return_value = {'hits': {'hits': []}}
        mock_save.return_value = {'result': 'created'}

        obj = {'url': 'http://example.com'}
        result = add(obj)

        self.assertTrue(result['success'])
        mock_save.assert_called_once_with(obj)

    @patch('app.main.lib.elastic_crud.OpenSearch')
    def test_get_by_doc_id_or_url(self, mock_opensearch):
        # Mock existing document in Elasticsearch
        mock_es = mock_opensearch.return_value
        mock_es.search.return_value = {'hits': {'hits': [{'id': '1', '_source': {'url': 'http://example.com', 'doc_id': '123'}}]}}

        # Test case where doc_id matches
        obj = {'doc_id': '123'}
        result = get_by_doc_id_or_url(obj)
        self.assertIsNotNone(result)
        self.assertEqual(result['doc_id'], '123')

        # Test case where url matches
        obj = {'url': 'http://example.com'}
        result = get_by_doc_id_or_url(obj)
        self.assertIsNotNone(result)
        self.assertEqual(result['url'], 'http://example.com')

        # Test case where neither doc_id nor url matches
        mock_es.search.return_value = {'hits': {'hits': []}}
        obj = {'doc_id': 'nonexistent-doc-id', 'url': 'http://nonexistent.com'}
        result = get_by_doc_id_or_url(obj)
        self.assertIsNone(result)

    @patch('app.main.lib.elastic_crud.OpenSearch')
    @patch('app.main.lib.elastic_crud.add')
    def test_get_object_existing(self, mock_add, mock_opensearch):
        # Scenario: Object exists in Elasticsearch
        mock_es = mock_opensearch.return_value
        mock_es.search.return_value = {'hits': {'hits': [{'id': '1', '_source': {'url': 'http://example.com', 'doc_id': '123'}}]}}

        obj = {'doc_id': '123'}
        result, temporary = get_object(obj)

        self.assertIsNotNone(result)
        self.assertFalse(temporary)
        mock_add.assert_not_called()

    @patch('app.main.lib.elastic_crud.OpenSearch')
    @patch('app.main.lib.elastic_crud.add')
    def test_get_object_temporary(self, mock_add, mock_opensearch):
        # Scenario: Object does not exist in Elasticsearch and is temporarily added
        mock_es = mock_opensearch.return_value
        mock_es.search.side_effect = [{'hits': {'hits': []}}, {'hits': {'hits': [{'id': '1', '_source': {'url': 'http://example.com', 'doc_id': '123'}}]}}]
        mock_add.return_value = None

        obj = {'url': 'http://example.com'}
        result, temporary = get_object(obj)

        self.assertIsNotNone(result)
        self.assertTrue(temporary)
        mock_add.assert_called_once()
        self.assertIn('doc_id', obj)


if __name__ == '__main__':
    unittest.main()
