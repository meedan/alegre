import unittest
import json
from flask import current_app as app
import redis
from sqlalchemy import text
from unittest.mock import patch

from app.main import db
from app.test.base import BaseTestCase
from app.main.model.context_hash import ContextHash
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.shared_models.video_model import VideoModel
class SharedModelStub(SharedModel):
  model_key = 'video'

  def load(self):
    pass

  def respond(self, task):
    return task

class TestVideoSimilarityBlueprint(BaseTestCase):
  def setUp(self):
    super().setUp()
    self.model = VideoModel('video')

  def test_basic_http_responses(self):
    url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
    import code;code.interact(local=dict(globals(), **locals())) 

    with patch('app.main.lib.shared_models.shared_model.SharedModel.get_client', ) as mock_get_shared_model_client:
      with patch('app.main.lib.shared_models.shared_model.SharedModel.get_shared_model_response', ) as mock_get_shared_model_response:
        mock_get_shared_model_client.return_value = SharedModelStub('video')
        mock_get_shared_model_response.return_value = {"url": url, "id": 123}
        response = self.client.post('/video/similarity/', data=json.dumps({
          'url': url,
          'context': {
            'team_id': 1,
            'project_media_id': 1
          }
        }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(result, {"url": url, "id": 123})

    with patch('app.main.lib.shared_models.shared_model.SharedModel.get_client', ) as mock_get_shared_model_client:
      with patch('app.main.lib.shared_models.shared_model.SharedModel.get_shared_model_response', ) as mock_get_shared_model_response:
        mock_get_shared_model_client.return_value = SharedModelStub('video')
        mock_get_shared_model_response.return_value = {"url": url, "id": 123}
        response = self.client.delete('/video/similarity/', data=json.dumps({
          'url': url,
          'context': {
            'team_id': 1,
            'project_media_id': 1
          }
        }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(result, {"url": url, "id": 123})

    with patch('app.main.lib.shared_models.shared_model.SharedModel.get_client', ) as mock_get_shared_model_client:
      with patch('app.main.lib.shared_models.shared_model.SharedModel.get_shared_model_response', ) as mock_get_shared_model_response:
        mock_get_shared_model_client.return_value = SharedModelStub('video')
        mock_get_shared_model_response.return_value = [{"url": url, "id": 123}]
        response = self.client.get('/video/similarity/', data=json.dumps({
          'url': url,
          'context': {
            'team_id': 1,
            'project_media_id': 1
          }
        }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(result, [{"url": url, "id": 123}])

    def test_get_tempfile(self):
        self.assertIsInstance(self.model.get_tempfile(), tempfile._TemporaryFileWrapper)

    def test_execute_command(self):
        self.assertIsInstance(self.model.execute_command("ls"), str)

    def test_load(self):
        self.assertIsInstance(self.directory, str)
        self.assertIsInstance(self.ffmpeg_dir, str)

    def test_delete(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        self.model.add({"url": url, "id": 1})
        result = self.model.delete({"url": url, "id": 1})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(sorted(result['requested'].keys()), ['id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['outfile'])

    def test_add(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        result = self.model.add({"url": url, "id": 1})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(sorted(result['requested'].keys()), ['id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['outfile'])

    def test_search(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        hash_key = ContextHash.query.all()[0].hash_key
        with patch('app.main.lib.shared_models.video_model.VideoModel.execute_command', ) as mock_execute_command:
            mock_execute_command.return_value = f"-0.088088 0.033167 /app/persistent_disk/{hash_key}/12342.tmk /app/persistent_disk/{hash_key}/12343.tmk\n1.000000 1.000000 /app/persistent_disk/{hash_key}/12343.tmk /app/persistent_disk/{hash_key}/12343.tmk\n"
            result = self.model.search({"url": url, "id": 1})
        self.assertIsInstance(result, list)
        self.assertEqual(sorted(result[0].keys()), ['filename', 'hash_key', 'media_id', 'threshold'])
        self.assertEqual(result[0], {'hash_key': 'a303bb3e3474e04ebe92816add72d032', 'threshold': '0.033167', 'filename': '/app/persistent_disk/a303bb3e3474e04ebe92816add72d032/12342.tmk', 'media_id': '12342'})

    def test_respond_delete(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        self.model.add({"url": url, "id": 1})
        result = self.model.respond({"url": url, "id": 1, "command": "delete"})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(sorted(result['requested'].keys()), ['id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['outfile'])

    def test_respond_add(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        result = self.model.respond({"url": url, "id": 1, "command": "add"})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(sorted(result['requested'].keys()), ['id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['outfile'])

    def test_respond_search(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        hash_key = ContextHash.query.all()[0].hash_key
        with patch('app.main.lib.shared_models.video_model.VideoModel.execute_command', ) as mock_execute_command:
            mock_execute_command.return_value = f"-0.088088 0.033167 /app/persistent_disk/{hash_key}/12342.tmk /app/persistent_disk/{hash_key}/12343.tmk\n1.000000 1.000000 /app/persistent_disk/{hash_key}/12343.tmk /app/persistent_disk/{hash_key}/12343.tmk\n"
            result = self.model.command({"url": url, "id": 1, "command": "search"})
        self.assertIsInstance(result, list)
        self.assertEqual(sorted(result[0].keys()), ['filename', 'hash_key', 'media_id', 'threshold'])
        self.assertEqual(result[0], {'hash_key': 'a303bb3e3474e04ebe92816add72d032', 'threshold': '0.033167', 'filename': '/app/persistent_disk/a303bb3e3474e04ebe92816add72d032/12342.tmk', 'media_id': '12342'})

    def test_tmk_dir(self):
        self.assertIsInstance(self.model.tmk_dir(), str)

    def test_tmk_query_command(self):
        self.assertIsInstance(self.model.tmk_query_command(), str)

    def test_tmk_hash_video_command(self):
        self.assertIsInstance(self.model.tmk_hash_video_command(), str)

    def test_tmk_directory(self):
        self.assertIsInstance(self.model.tmk_directory(ContextHash(hash_key="blah", context={})), str)

    def test_tmk_file_path(self):
        self.assertIsInstance(self.model.tmk_file_path({"id": 1}, ContextHash(hash_key="blah", context={})), str)
        
    def test_get_fullpath_files(self):
        self.assertIsInstance(self.model.get_fullpath_files(ContextHash(hash_key="blah", context={})), list)
        with patch('os.listdir', ) as mock_list:
            with patch('os.path.isfile', ) as mock_is_file:
                mock_list.return_value = ['/app/persistent_disk/blah/1.tmk']
                mock_is_file.return_value = True
                result = self.model.get_fullpath_files(ContextHash(hash_key="blah", context={}))
        self.assertEqual(result, ['/app/persistent_disk/blah/1.tmk'])

    def test_media_id_from_filepath(self):
        self.assertEqual(self.model.media_id_from_filepath('/foo/bar/baz.tmk'), 'baz')

    def parse_search_results(self):
        result = "-0.088088 0.033167 /app/persistent_disk/blah/12342.tmk /app/persistent_disk/blah/12343.tmk\n1.000000 1.000000 /app/persistent_disk/blah/12343.tmk /app/persistent_disk/blah/12343.tmk\n"
        response = self.model.parse_search_results(result, ContextHash(hash_key="blah", context={}))
        self.assertEqual(response, [{'hash_key': 'blah', 'threshold': '0.033167', 'filename': '/app/persistent_disk/blah/12342.tmk', 'media_id': '12342'}, {'hash_key': 'blah', 'threshold': '1.000000', 'filename': '/app/persistent_disk/blah/12343.tmk', 'media_id': '12343'}])

if __name__ == '__main__':
  unittest.main()