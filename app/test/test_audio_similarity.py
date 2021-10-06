import tempfile
import unittest
import json
from flask import current_app as app
import redis
from sqlalchemy import text
from unittest.mock import patch

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.shared_models.audio_model import AudioModel
class SharedModelStub(SharedModel):
  model_key = 'audio'

  def load(self):
    pass

  def respond(self, task):
    return task

class TestAudioSimilarityBlueprint(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.model = AudioModel('audio')

    def test_basic_http_responses_with_doc_id(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        with patch('app.main.lib.shared_models.shared_model.SharedModel.get_client', ) as mock_get_shared_model_client:
            with patch('app.main.lib.shared_models.shared_model.SharedModel.get_shared_model_response', ) as mock_get_shared_model_response:
                mock_get_shared_model_client.return_value = SharedModelStub('audio')
                mock_get_shared_model_response.return_value = {"url": url, "project_media_id": 123}
                response = self.client.post('/audio/similarity/', data=json.dumps({
                    'url': url,
                    'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8",
                    'context': {
                        'team_id': 1,
                        'has_custom_id': True
                    }
                }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(result, {"url": url, "project_media_id": 123})
        with patch('app.main.lib.shared_models.shared_model.SharedModel.get_client', ) as mock_get_shared_model_client:
            with patch('app.main.lib.shared_models.shared_model.SharedModel.get_shared_model_response', ) as mock_get_shared_model_response:
                mock_get_shared_model_client.return_value = SharedModelStub('audio')
                mock_get_shared_model_response.return_value = {"result": [{"hash_key": "6393db3d6d5c181aa43dd925539a15e7", "context": {"blah": 1, "project_media_id": "12343"}, "score": "0.033167", "filename": "/app/persistent_disk/6393db3d6d5c181aa43dd925539a15e7/12342.tmk"}, {"hash_key": "6393db3d6d5c181aa43dd925539a15e7", "context": {"blah": 1, "project_media_id": "12343"}, "score": "1.000000", "filename": "/app/persistent_disk/6393db3d6d5c181aa43dd925539a15e7/12343.tmk"}]}
                response = self.client.get('/audio/similarity/', data=json.dumps({
                    'url': url,
                    'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8",
                    'context': {
                        'team_id': 1,
                        'has_custom_id': True
                    }
                }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(result, {'result': [{'hash_key': '6393db3d6d5c181aa43dd925539a15e7', 'context': {'blah': 1, 'project_media_id': '12343'}, 'score': '0.033167', 'filename': '/app/persistent_disk/6393db3d6d5c181aa43dd925539a15e7/12342.tmk'}, {'hash_key': '6393db3d6d5c181aa43dd925539a15e7', 'context': {'blah': 1, 'project_media_id': '12343'}, 'score': '1.000000', 'filename': '/app/persistent_disk/6393db3d6d5c181aa43dd925539a15e7/12343.tmk'}]})

    def test_basic_http_responses(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        with patch('app.main.lib.shared_models.shared_model.SharedModel.get_client', ) as mock_get_shared_model_client:
            with patch('app.main.lib.shared_models.shared_model.SharedModel.get_shared_model_response', ) as mock_get_shared_model_response:
                mock_get_shared_model_client.return_value = SharedModelStub('audio')
                mock_get_shared_model_response.return_value = {"url": url, "project_media_id": 123}
                response = self.client.post('/audio/similarity/', data=json.dumps({
                    'url': url,
                    'project_media_id': 1,
                    'context': {
                        'team_id': 1,
                    }
                }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(result, {"url": url, "project_media_id": 123})
        with patch('app.main.lib.shared_models.shared_model.SharedModel.get_client', ) as mock_get_shared_model_client:
            with patch('app.main.lib.shared_models.shared_model.SharedModel.get_shared_model_response', ) as mock_get_shared_model_response:
                mock_get_shared_model_client.return_value = SharedModelStub('audio')
                mock_get_shared_model_response.return_value = {"result": [{"hash_key": "6393db3d6d5c181aa43dd925539a15e7", "context": {"blah": 1, "project_media_id": "12343"}, "score": "0.033167", "filename": "/app/persistent_disk/6393db3d6d5c181aa43dd925539a15e7/12342.tmk"}, {"hash_key": "6393db3d6d5c181aa43dd925539a15e7", "context": {"blah": 1, "project_media_id": "12343"}, "score": "1.000000", "filename": "/app/persistent_disk/6393db3d6d5c181aa43dd925539a15e7/12343.tmk"}]}
                response = self.client.get('/audio/similarity/', data=json.dumps({
                    'url': url,
                    'project_media_id': 1,
                    'context': {
                        'team_id': 1,
                    }
                }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(result, {'result': [{'hash_key': '6393db3d6d5c181aa43dd925539a15e7', 'context': {'blah': 1, 'project_media_id': '12343'}, 'score': '0.033167', 'filename': '/app/persistent_disk/6393db3d6d5c181aa43dd925539a15e7/12342.tmk'}, {'hash_key': '6393db3d6d5c181aa43dd925539a15e7', 'context': {'blah': 1, 'project_media_id': '12343'}, 'score': '1.000000', 'filename': '/app/persistent_disk/6393db3d6d5c181aa43dd925539a15e7/12343.tmk'}]})

    def test_get_tempfile(self):
        self.assertIsInstance(self.model.get_tempfile(), tempfile._TemporaryFileWrapper)

    def test_execute_command(self):
        self.assertIsInstance(self.model.execute_command("ls"), str)

    def test_load(self):
        self.model.load()
        self.assertIsInstance(self.model.directory, str)
        self.assertIsInstance(self.model.ffmpeg_dir, str)

    def test_delete_by_doc_id(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        self.model.load()
        self.model.add({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"has_custom_id": True}})
        result = self.model.delete({"url": url, "project_media_id": 1})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(sorted(result['requested'].keys()), ['project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['deleted', 'url'])

    def test_add_by_doc_id(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        self.model.load()
        result = self.model.add({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"has_custom_id": True}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result', 'success'])
        self.assertEqual(sorted(result['requested'].keys()), ['context', 'doc_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['url'])

    def test_search_by_doc_id(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        self.model.load()
        hash_key = "blah"
        with patch('app.main.lib.shared_models.audio_model.AudioModel.search_by_context', ) as mock_search_by_context:
            mock_search_by_context.return_value = [{"folder": "blah", "filepath": "12342", "context": [{'blah': 1, 'project_media_id': 12342}]}, {"folder": "blah", "filepath": "12343", "context": [{'blah': 1, 'project_media_id': 12343}]}]
            self.model.add({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"blah": 1, "has_custom_id": True, 'project_media_id': 12343}})
            result = self.model.search({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"blah": 1, "has_custom_id": True, 'project_media_id': 12343}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result["result"][0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'score', 'url'])
        self.assertEqual(result["result"][0]['id'], 1)
        self.assertEqual(result["result"][0]['doc_id'], 'Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8')
        self.assertEqual(result["result"][0]['url'], 'file:///app/app/test/data/eddy_wally_wow.mp3')
        self.assertEqual(result["result"][0]['context'], [{'blah': 1, 'has_custom_id': True, 'project_media_id': 12343}])

    def test_delete(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        self.model.load()
        self.model.add({"url": url, "project_media_id": 1})
        result = self.model.delete({"url": url, "project_media_id": 1})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(sorted(result['requested'].keys()), ['project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['deleted', 'url'])

    def test_add(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        self.model.load()
        result = self.model.add({"url": url, "project_media_id": 1})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result', 'success'])
        self.assertEqual(sorted(result['requested'].keys()), ['project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['url'])

    def test_add_wav(self):
        url = 'file:///app/app/test/data/sample.wav'
        self.model.load()
        result = self.model.add({"url": url, "project_media_id": 1})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result', 'success'])
        self.assertEqual(sorted(result['requested'].keys()), ['project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['url'])

    def test_search(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        self.model.load()
        hash_key = "blah"
        with patch('app.main.lib.shared_models.audio_model.AudioModel.search_by_context', ) as mock_search_by_context:
            mock_search_by_context.return_value = [{"folder": "blah", "filepath": "12342", "context": [{'blah': 1, 'project_media_id': 12342}]}, {"folder": "blah", "filepath": "12343", "context": [{'blah': 1, 'project_media_id': 12343}]}]
            self.model.add({"url": url, "project_media_id": 1, "context": {"blah": 1, 'project_media_id': 12343}})
            result = self.model.search({"url": url, "project_media_id": 1, "context": {"blah": 1, 'project_media_id': 12343}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result["result"][0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'score', 'url'])
        self.assertEqual(result["result"][0]['id'], 1)
        self.assertEqual(result["result"][0]['url'], 'file:///app/app/test/data/eddy_wally_wow.mp3')
        self.assertEqual(result["result"][0]['context'], [{'blah': 1, 'has_custom_id': True, 'project_media_id': 12343}])

    def test_respond_delete(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        self.model.load()
        self.model.add({"url": url, "id": 1})
        result = self.model.respond({"url": url, "project_media_id": 1, "command": "delete"})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(sorted(result['requested'].keys()), ['command', 'project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['deleted', 'url'])

    def test_respond_add(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        self.model.load()
        result = self.model.respond({"url": url, "project_media_id": 1, "command": "add"})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result', 'success'])
        self.assertEqual(sorted(result['requested'].keys()), ['command', 'project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['url'])

    def test_respond_search(self):
        url = 'file:///app/app/test/data/eddy_wally_wow.mp3'
        self.model.load()
        hash_key = "blah"
        with patch('app.main.lib.shared_models.audio_model.AudioModel.search_by_context', ) as mock_search_by_context:
            mock_search_by_context.return_value = [{"folder": "blah", "filepath": "12342", "context": [{'blah': 1, 'project_media_id': 12342}]}, {"folder": "blah", "filepath": "12343", "context": [{'blah': 1, 'project_media_id': 12343}]}]
            self.model.respond({"url": url, "project_media_id": 1, "command": "add", "context": {"blah": 1, 'project_media_id': 12343}})
            result = self.model.respond({"url": url, "project_media_id": 1, "command": "search", "context": {"blah": 1, 'project_media_id': 12343}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result["result"][0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'score', 'url'])
        self.assertEqual(result["result"][0]['id'], 1)
        self.assertEqual(result["result"][0]['url'], 'file:///app/app/test/data/eddy_wally_wow.mp3')
        self.assertEqual(result["result"][0]['context'], [{'blah': 1, 'has_custom_id': True, 'project_media_id': 12343}])

if __name__ == '__main__':
  unittest.main()
