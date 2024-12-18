from unittest.mock import ANY
import unittest
from unittest.mock import patch, MagicMock
from app.main.lib.helpers import merge_dict_lists
from app.main.lib.media_crud import tmk_file_path, save, delete, add, get_by_doc_id_or_url, get_object, get_context_for_search, get_blocked_presto_response, get_async_presto_response
from app.main import db
from flask import current_app as app
from app.main.lib.presto import Presto, PRESTO_MODEL_MAP
from app.main.model.audio import Audio
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound
import urllib.error
import json

class TestMediaCrud(unittest.TestCase):
    def test_empty_lists(self):
        self.assertEqual(merge_dict_lists([], []), [])

    def test_non_overlapping_lists(self):
        list1 = [{'key1': 'value1'}, {'key2': 'value2'}]
        list2 = [{'key3': 'value3'}]
        self.assertTrue({'key2': 'value2'} in merge_dict_lists(list1, list2))
        self.assertTrue({'key3': 'value3'} in merge_dict_lists(list1, list2))
        self.assertTrue({'key1': 'value1'} in merge_dict_lists(list1, list2))

    def test_overlapping_lists(self):
        list1 = [{'key': 'value1'}, {'key': 'value2'}]
        list2 = [{'key': 'value1'}]
        self.assertTrue({'key': 'value1'} in merge_dict_lists(list1, list2))
        self.assertTrue({'key': 'value2'} in merge_dict_lists(list1, list2))

    def test_nested_lists(self):
        list1 = [{'key': ['value1', 'value2']}]
        list2 = [{'key': ['value2', 'value3']}]
        self.assertTrue({'key': ['value1', 'value2']} in merge_dict_lists(list1, list2))
        self.assertTrue({'key': ['value2', 'value3']} in merge_dict_lists(list1, list2))

    def test_different_data_types(self):
        list1 = [{'key': 1}, {'key': 'value'}]
        list2 = [{'key': 1.0}]
        expected = [{'key': 'value'}, {'key': 1}]
        self.assertTrue({'key': 'value'} in merge_dict_lists(list1, list2))
        self.assertTrue({'key': 1} in merge_dict_lists(list1, list2))

    def test_single_element_lists(self):
        list1 = [{'key': 'value'}]
        list2 = [{'key': 'value'}]
        expected = [{'key': 'value'}]
        self.assertEqual(merge_dict_lists(list1, list2), expected)

    @patch('app.main.lib.media_crud.db.session.commit')
    @patch('app.main.lib.media_crud.db.session.add')
    @patch('app.main.lib.media_crud.db.session.query')
    def test_save_existing_object(self, mock_query, mock_add, mock_commit):
        # Mocking an existing object found by the query
        mock_model = MagicMock()
        mock_obj = Audio(url="http://example.com", context=[{"foo": "bar"}, {"baz": "bat"}], hash_value="new_hash")
        mock_model.query.filter.return_value.one.return_value = mock_obj

        # Calling save function with an object having the same URL
        new_obj = Audio(url="http://example.com", context=[{"foo": "bar"}, {"baz": "bat"}], hash_value="new_hash")
        save(new_obj, Audio)

        # Check if existing object is updated and committed
        self.assertTrue(mock_obj.context == [{"foo": "bar"}, {"baz": "bat"}])
        mock_commit.assert_called_once()

    @patch('app.main.lib.media_crud.db.session.commit')
    @patch('app.main.lib.media_crud.db.session.add')
    @patch('app.main.lib.media_crud.db.session.query')
    def test_save_new_object(self, mock_query, mock_add, mock_commit):
        # Mocking NoResultFound to simulate no existing object
        mock_model = MagicMock()
        mock_query.side_effect = NoResultFound

        # Calling save function with a new object
        new_obj = MagicMock(url="http://newexample.com", context="new_context", hash_value="new_hash")
        save(new_obj, mock_model)

        # Check if new object is added and committed
        mock_add.assert_called_with(new_obj)
        mock_commit.assert_called_once()

    @patch('app.main.lib.media_crud.db.session.rollback')
    @patch('app.main.lib.media_crud.db.session.commit')
    @patch('app.main.lib.media_crud.db.session.add')
    @patch('app.main.lib.media_crud.db.session.query')
    def test_save_exception_handling(self, mock_query, mock_add, mock_commit, mock_rollback):
        # Mocking an exception during the save process
        mock_model = MagicMock()
        mock_query.side_effect = Exception

        new_obj = MagicMock(url="http://exceptionexample.com", context="new_context", hash_value="new_hash")

        # Expecting an exception to be raised
        with self.assertRaises(Exception):
            save(new_obj, mock_model)

        # Check if transaction is rolled back
        self.assertEqual(mock_rollback.call_count, 11)

    @patch('app.main.lib.media_crud.get_by_doc_id_or_url')
    @patch('app.main.lib.media_crud.db.session.query')
    def test_delete(self, mock_query, mock_get_by_doc_id_or_url):
        # Model for the test
        model = Audio
        mock_filter = MagicMock()
        # Configure the filter mock to return a mock for delete
        mock_delete = MagicMock(return_value=True)
        mock_filter.return_value.delete.return_value = mock_delete.return_value

        # Set the query mock to return the filter mock
        mock_query.return_value.filter.return_value = mock_filter.return_value

        # Test case 1: Object found and context exists, context length > 1
        mock_obj = Audio(id=1, doc_id="123", url="http://example.com/url", chromaprint_fingerprint=[-713337002, -1778428074, -1778560170, -1778560650], context=[{"foo": "bar"}])
        mock_get_by_doc_id_or_url.return_value = mock_obj
        task = {'url': "http://example.com/url", 'context': {"foo": "bar"}}
        result = delete(task, model)
        self.assertEqual(result['result']['deleted'], True)
        self.assertEqual(result['result']['url'], "http://example.com/url")

        # Test case 2: Object found and context does not exist, context length == 1
        mock_get_by_doc_id_or_url.return_value = mock_obj
        result = delete(task, model)
        self.assertEqual(result['result']['deleted'], True)
        self.assertEqual(result['result']['url'], "http://example.com/url")

        # Test case 3: Object found, context does not exist
        mock_filter = MagicMock()
        # Configure the filter mock to return a mock for delete
        mock_delete = MagicMock(return_value=False)
        mock_filter.return_value.delete.return_value = mock_delete.return_value

        # Set the query mock to return the filter mock
        mock_query.return_value.filter.return_value = mock_filter.return_value
        result = delete(task, model)
        self.assertEqual(result['result']['deleted'], False)
        self.assertEqual(result['result']['url'], "http://example.com/url")

        # Test case 4: Object not found
        mock_get_by_doc_id_or_url.return_value = None
        result = delete(task, model)
        self.assertEqual(result['result']['deleted'], False)
        self.assertEqual(result['result']['url'], "http://example.com/url")


    @patch('app.main.lib.media_crud.db.session.query')
    @patch('app.main.lib.media_crud.save')
    @patch('app.main.model.audio.Audio.from_task_data')
    def test_add_success(self, mock_from_task_data, mock_save, mock_query):
        # Setup
        mock_model = MagicMock()
        mock_obj = Audio(url="http://example.com", context=[{"foo": "bar"}, {"baz": "bat"}], hash_value="new_hash")
        mock_model.query.filter.return_value.one.return_value = mock_obj
        task = {'url': 'http://example.com/image.jpg'}
        model = Audio
        modifiable_fields = ["hash_value", "chromaprint_fingerprint"]
        mock_obj = MagicMock(url=task['url'])
        mock_from_task_data.return_value = mock_obj
        mock_save.return_value = mock_obj

        # Test
        result, _ = add(task, model, modifiable_fields)

        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['requested'], task)
        self.assertEqual(result['result']['url'], task['url'])
        mock_from_task_data.assert_called_once_with(task, ANY)
        mock_save.assert_called_once_with(mock_obj, model, modifiable_fields)

    @patch('app.main.lib.media_crud.db.session.query')
    @patch('app.main.lib.media_crud.save')
    @patch('app.main.model.audio.Audio.from_task_data')
    def test_add_integrity_error(self, mock_from_task_data, mock_save, mock_query):
        # Setup
        mock_model = MagicMock()
        mock_obj = Audio(url="http://example.com", context=[{"foo": "bar"}, {"baz": "bat"}], hash_value="new_hash")
        mock_model.query.filter.return_value.one.return_value = mock_obj
        task = {'url': 'http://example.com/image.jpg'}
        model = Audio
        modifiable_fields = ["hash_value", "chromaprint_fingerprint"]
        mock_obj = MagicMock(url=task['url'])
        mock_from_task_data.return_value = mock_obj
        mock_save.side_effect = sqlalchemy.exc.IntegrityError(None, None, None)

        # Test
        result, _ = add(task, model, modifiable_fields)

        # Assert
        self.assertFalse(result['success'])
        self.assertEqual(result['requested'], task)
        self.assertEqual(result['result']['url'], task['url'])
        mock_from_task_data.assert_called_once_with(task, ANY)
        mock_save.assert_called_once_with(mock_obj, model, modifiable_fields)

    @patch('app.main.lib.media_crud.db.session.query')
    def test_get_by_doc_id_or_url(self, mock_query):
        # Create a mock return value for the query
        mock_model = MagicMock()
        mock_model.filter.return_value.all.return_value = [Audio(id=1, doc_id="123", url="http://example.com/url", chromaprint_fingerprint=[-713337002, -1778428074, -1778560170, -1778560650], context=[{"foo": "bar"}])]

        mock_query.return_value = mock_model

        # Test case where doc_id matches
        task_with_doc_id = {'doc_id': '123'}
        result = get_by_doc_id_or_url(task_with_doc_id, Audio)
        self.assertIsNotNone(result)
        self.assertEqual(result.doc_id, '123')

        # Reset mock
        mock_model.reset_mock()

        # Test case where url matches
        task_with_url = {'url': 'http://example.com/url'}
        result = get_by_doc_id_or_url(task_with_url, Audio)
        self.assertIsNotNone(result)
        self.assertEqual(result.url, 'http://example.com/url')

        # Reset mock
        mock_model.reset_mock()

        # Test case where neither doc_id nor url matches
        task_with_no_match = {'doc_id': 'nonexistent-doc-id', 'url': 'http://nonexistent.com'}
        mock_model.filter.return_value.all.return_value = []
        result = get_by_doc_id_or_url(task_with_no_match, Audio)
        self.assertIsNone(result)


    @patch('app.main.lib.media_crud.get_by_doc_id_or_url')
    @patch('app.main.lib.media_crud.add')
    def test_get_object_existing(self, mock_add, mock_get_by_doc_id_or_url):
        # Scenario: Object exists in the database
        mock_obj = MagicMock()
        mock_get_by_doc_id_or_url.return_value = mock_obj

        task = {'doc_id': 'some-doc-id'}
        model = MagicMock()

        obj, temporary = get_object(task, model)

        self.assertEqual(obj, mock_obj)
        self.assertFalse(temporary)
        mock_add.assert_not_called()

    @patch('app.main.lib.media_crud.get_by_doc_id_or_url')
    @patch('app.main.lib.media_crud.add')
    def test_get_object_temporary(self, mock_add, mock_get_by_doc_id_or_url):
        # Scenario: Object does not exist and is temporarily added
        mock_get_by_doc_id_or_url.side_effect = [None, MagicMock()]
        mock_add.return_value = None

        task = {'url': 'http://example.com'}
        model = MagicMock()

        obj, temporary = get_object(task, model)

        self.assertIsNotNone(obj)
        self.assertTrue(temporary)
        mock_add.assert_called_once()
        # Ensure that a doc_id is set if it wasn't initially provided
        self.assertIn('doc_id', task)

    def test_context_present(self):
        task = {'context': {'key1': 'value1', 'content_type': 'type1', 'project_media_id': 'id1'}}
        expected_context = {'content_type': 'type1', 'key1': 'value1', 'project_media_id': 'id1'}
        self.assertEqual(get_context_for_search(task), expected_context)

    def test_context_present_with_match_across_content_types(self):
        task = {'context': {'key1': 'value1', 'content_type': 'type1', 'project_media_id': 'id1'}, 'match_across_content_types': True}
        expected_context = {'key1': 'value1', 'project_media_id': 'id1'}
        self.assertEqual(get_context_for_search(task), expected_context)

    def test_context_not_present(self):
        task = {}
        expected_context = {}
        self.assertEqual(get_context_for_search(task), expected_context)

    def test_context_removal_of_project_media_id(self):
        task = {'context': {'key1': 'value1', 'project_media_id': 'id1'}}
        expected_context = {'key1': 'value1', 'project_media_id': 'id1'}
        self.assertEqual(get_context_for_search(task), expected_context)

    @patch('app.main.lib.presto.Presto.blocked_response')
    @patch('app.main.lib.presto.Presto.send_request')
    @patch('app.main.lib.media_crud.get_context_for_search')
    @patch('app.main.lib.media_crud.get_object')
    def test_get_blocked_presto_response(self, mock_get_object, mock_get_context_for_search, mock_send_request, mock_blocked_response):
        # Setup
        task = {"url": "http://example.com", "modality": "audio"}
        model = MagicMock()
        modality = "audio"

        # Mock return values
        mock_get_object.return_value = (MagicMock(), False)
        mock_get_context_for_search.return_value = {"context_key": "context_value"}
        mock_send_request.return_value = MagicMock(text=json.dumps({
            'message': 'Message pushed successfully',
            'queue': 'video__Model',
            'body': {
                'callback_url': 'http://alegre:3100/presto/receive/add_item/video',
                'id': "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8",
                'url': 'http://example.com/chair-19-sd-bar.mp4',
                'text': None,
                'raw': {
                    'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                    'url': 'http://example.com/chair-19-sd-bar.mp4',
                }
            }
        }))
        mock_blocked_response.return_value = {"blocked_response_key": "blocked_response_value"}

        # Call the function
        obj, temporary, context, response = get_blocked_presto_response(task, model, modality)

        # Assertions
        mock_get_object.assert_called_once_with(task, model)
        mock_get_context_for_search.assert_called_once_with(task)
        mock_send_request.assert_called_once()
        mock_blocked_response.assert_called_once()

        self.assertFalse(temporary)
        self.assertEqual(context, {"context_key": "context_value"})
        self.assertEqual(response, {"blocked_response_key": "blocked_response_value"})

    @patch('app.main.lib.presto.Presto.send_request')
    @patch('app.main.lib.media_crud.get_object')
    @patch('app.main.lib.media_crud.get_context_for_search')
    def test_get_async_presto_response(self, mock_get_context_for_search, mock_get_object, mock_send_request):
        # Prepare the data and mocks
        test_task = {"doc_id": "some_doc_id", "url": "http://example.com", "final_task": "search"}
        test_model = MagicMock()
        test_modality = "audio"
        mock_obj = MagicMock()
        mock_temporary = False
        mock_context = {"some": "context"}
        mock_response = json.dumps({
            'message': 'Message pushed successfully',
            'queue': 'video__Model',
            'body': {
                'callback_url': 'http://alegre:3100/presto/receive/add_item/video',
                'id': "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8",
                'url': 'http://example.com/chair-19-sd-bar.mp4',
                'text': None,
                'raw': {
                    'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                    'url': 'http://example.com/chair-19-sd-bar.mp4',
                }
            }
        })

        # Set return values for mocks
        mock_get_object.return_value = (mock_obj, mock_temporary)
        mock_get_context_for_search.return_value = mock_context
        mock_send_request.return_value = MagicMock(text=mock_response)

        # Call the function under test
        result = get_async_presto_response(test_task, test_model, test_modality)[0]

        # Assert that the mocks were called correctly
        mock_get_object.assert_called_once_with(test_task, test_model)
        mock_send_request.assert_called_once_with(
            app.config['PRESTO_HOST'],
            PRESTO_MODEL_MAP[test_modality],
            Presto.add_item_callback_url(app.config['ALEGRE_HOST'], test_modality),
            test_task,
            False
        )

        # Assert the expected result
        self.assertEqual(result, json.loads(mock_response))

    def test_tmk_file_path(self):
        self.assertIsInstance(tmk_file_path("foo", "bar"), str)

if __name__ == '__main__':
    unittest.main()
