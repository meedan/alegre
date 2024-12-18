import unittest
from unittest.mock import patch, MagicMock
from flask import current_app as app
from opensearchpy import OpenSearch
import json
import uuid

from app.main.lib.elastic_crud import (
    get_object_by_doc_id,
    get_object,
    get_context_for_search,
    get_presto_request_response,
    requires_encoding,
    get_blocked_presto_response,
    get_async_presto_response,
    parse_task_search
)

class TestElasticCrud(unittest.TestCase):
    @patch('app.main.lib.elastic_crud.get_by_doc_id')
    def test_get_object_by_doc_id(self, mock_get_by_doc_id):
        mock_get_by_doc_id.return_value = {'doc_id': '123', 'content': 'test content'}

        result = get_object_by_doc_id('123')
        self.assertEqual(result, {'doc_id': '123', 'content': 'test content'})
        mock_get_by_doc_id.assert_called_once_with('123')

    @patch('app.main.lib.elastic_crud.store_document')
    def test_get_object(self, mock_store_document):
        task = {'doc_id': '123', 'content': 'test content'}
        model = MagicMock()

        result, temporary = get_object(task, model)
        self.assertFalse(temporary)
        self.assertEqual(result['doc_id'], '123')
        self.assertEqual(result['content'], 'test content')
        mock_store_document.assert_called_once_with(task, '123', None)

    def test_get_context_for_search(self):
        task = {'context': {'key1': 'value1', 'content_type': 'type1', 'project_media_id': 'id1'}}
        expected_context = {'content_type': 'type1', 'key1': 'value1', 'project_media_id': 'id1'}
        self.assertEqual(get_context_for_search(task), expected_context)

        task = {'context': {'key1': 'value1', 'content_type': 'type1', 'project_media_id': 'id1'}, 'match_across_content_types': True}
        expected_context = {'key1': 'value1', 'project_media_id': 'id1'}
        self.assertEqual(get_context_for_search(task), expected_context)

        task = {}
        expected_context = {}
        self.assertEqual(get_context_for_search(task), expected_context)

    @patch('app.main.lib.elastic_crud.Presto.send_request')
    def test_get_presto_request_response(self, mock_send_request):
        mock_send_request.return_value = MagicMock(text=json.dumps({
            'message': 'Message pushed successfully',
            'queue': 'mean_tokens__Model',
            'body': {'doc_id': '123'}
        }))

        task = {'doc_id': '123', 'content': 'test content'}
        modality = 'meantokens'
        callback_url = 'http://example.com/callback'

        result = get_presto_request_response(modality, callback_url, task)
        self.assertEqual(result['message'], 'Message pushed successfully')
        self.assertEqual(result['queue'], 'mean_tokens__Model')
        self.assertEqual(result['body']['doc_id'], '123')

    def test_requires_encoding(self):
        obj = {'models': ['model1', 'model2'], 'model_model1': 'encoded_data'}
        self.assertTrue(requires_encoding(obj))

        obj = {'models': ['model1'], 'model_model1': 'encoded_data'}
        self.assertFalse(requires_encoding(obj))

        obj = {'models': ['openai-text-embedding-ada-002']}
        self.assertFalse(requires_encoding(obj))


    @patch('app.main.lib.elastic_crud.Presto.blocked_response')
    @patch('app.main.lib.elastic_crud.Presto.send_request')
    @patch('app.main.lib.elastic_crud.store_document')
    def test_get_blocked_presto_response(self, mock_store_document, mock_send_request, mock_blocked_response):
        mock_send_request.return_value = MagicMock(text=json.dumps({
            'message': 'Message pushed successfully',
            'queue': 'mean_tokens__Model',
            'body': {'doc_id': '123'}
        }))

        task = {'url': 'http://example.com', 'models': ['opensearch', 'xlm-r-bert-base-nli-stsb-mean-tokens'], 'context': {'foo': 'bar'}}
        model = MagicMock()
        modality = 'meantokens'
        mock_blocked_response.return_value = task
        result = get_blocked_presto_response(task, model, modality)
        self.assertIsNotNone(result)
        self.assertEqual(result[0]['doc_id'], task['doc_id'])
        mock_store_document.assert_called()
        mock_send_request.assert_called()

    @patch('app.main.lib.elastic_crud.Presto.send_request')
    @patch('app.main.lib.elastic_crud.store_document')
    def test_get_async_presto_response(self, mock_store_document, mock_send_request):
        mock_send_request.return_value = MagicMock(text=json.dumps({
            'message': 'Message pushed successfully',
            'queue': 'mean_tokens__Model',
            'body': {'doc_id': '123'}
        }))

        task = {'url': 'http://example.com', 'context': {'foo': 'bar'}}
        model = MagicMock()
        modality = 'meantokens'

        result = get_async_presto_response(task, model, modality)
        self.assertIsNotNone(result)

    def test_parse_task_search(self):
        task = {'body': {'raw': {'threshold': 0.5, 'limit': 10}, 'result': {'hash_value': 'hash123'}, 'context': {'key1': 'value1'}}}
        body, threshold, limit = parse_task_search(task)
        self.assertEqual(body['hash_value'], 'hash123')
        self.assertEqual(threshold, 0.5)
        self.assertEqual(limit, 10)

        task = {'raw': {}, 'threshold': 0.3, 'limit': 5, 'context': {'key1': 'value1'}}
        body, threshold, limit = parse_task_search(task)
        self.assertEqual(threshold, 0.3)
        self.assertEqual(limit, 5)

if __name__ == '__main__':
    unittest.main()
