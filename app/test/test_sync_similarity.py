import unittest
import json
from opensearchpy import helpers, OpenSearch, TransportError
from flask import current_app as app
from unittest.mock import Mock, patch
import numpy as np
import redis

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel
from unittest.mock import patch
from app.main.model.audio import Audio
from app.main.lib.shared_models.audio_model import AudioModel
class TestSyncSimilarityBlueprint(BaseTestCase):
    def setUp(self):
        super().setUp()
        first_print = 49805440634311326
        self.model = AudioModel('audio')

    def tearDown(self): # done in our pytest fixture after yield
        db.session.remove()
        db.drop_all()

    def test_audio_basic_http_responses_with_doc_id(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        with patch('requests.post') as mock_post_request:
            r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
            r.delete(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
            r.lpush(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"body": {"result": {"hash_value": [1,2,3]}}}))
            mock_response = Mock()
            mock_response.text = json.dumps({
                'message': 'Message pushed successfully',
                'queue': 'audio__Model',
                'body': {
                    'callback_url': 'http://alegre:3100/presto/receive/add_item/audio',
                    'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                    'url': 'http://example.com/blah.mp3',
                    'text': None,
                    'raw': {
                        'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                        'url': 'http://example.com/blah.mp3'
                    }
                }
            })
            mock_post_request.return_value = mock_response
            response = self.client.post('/similarity/sync/audio', data=json.dumps({
                'url': url,
                'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                'context': {
                    'team_id': 1,
                }
            }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['doc_id'], '1c63abe0-aeb4-4bac-8925-948b69c32d0d')
        self.assertEqual(result["result"][0]['url'], 'file:///app/app/test/data/test_audio_1.mp3')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

    def test_audio_basic_http_responses(self):
        url = 'http://example.com/blah.mp3'
        with patch('requests.post') as mock_post_request:
            r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
            r.delete(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
            r.lpush(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"body": {"result": {"hash_value": [1,2,3]}}}))
            mock_response = Mock()
            mock_response.text = json.dumps({
                'message': 'Message pushed successfully',
                'queue': 'audio__Model',
                'body': {
                    'callback_url': 'http://alegre:3100/presto/receive/add_item/audio',
                    'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                    'url': 'http://example.com/blah.mp3',
                    'text': None,
                    'raw': {
                        'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                        'url': 'http://example.com/blah.mp3'
                    }
                }
            })
            mock_post_request.return_value = mock_response
            response = self.client.post('/similarity/sync/audio', data=json.dumps({
                'url': url,
                'project_media_id': 1,
                'context': {
                    'team_id': 1,
                }
            }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['url'], 'http://example.com/blah.mp3')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

    def test_image_basic_http_responses_with_doc_id(self):
        url = 'file:///app/app/test/data/lenna-512.jpg'
        with patch('requests.post') as mock_post_request:
            with patch('app.main.lib.image_similarity.execute_command') as mock_db_response:
                mock_db_response.return_value = [(1, "1c63abe0-aeb4-4bac-8925-948b69c32d0d", 49805440634311326, 'http://example.com/lenna-512.png', [{'team_id': 1}], 1.0)]
                r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
                r.delete(f"image_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
                r.lpush(f"image_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"body": {"hash_value": 49805440634311326}}))
                mock_response = Mock()
                mock_response.text = json.dumps({
                    'message': 'Message pushed successfully',
                    'queue': 'image__Model',
                    'body': {
                        'callback_url': 'http://alegre:3100/presto/receive/add_item/image',
                        'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                        'url': 'http://example.com/lenna-512.png',
                        'text': None,
                        'raw': {
                            'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                            'url': 'http://example.com/lenna-512.png'
                        }
                    }
                })
                mock_post_request.return_value = mock_response
                response = self.client.post('/similarity/sync/image', data=json.dumps({
                    'url': url,
                    'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                    'context': {
                        'team_id': 1,
                    }
                }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['context', 'doc_id', 'id', 'model', 'phash', 'score', 'url'])
        self.assertEqual(result["result"][0]['doc_id'], '1c63abe0-aeb4-4bac-8925-948b69c32d0d')
        self.assertEqual(result["result"][0]['url'], 'http://example.com/lenna-512.png')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

    def test_image_basic_http_responses(self):
        url = 'http://example.com/lenna-512.png'
        with patch('requests.post') as mock_post_request:
            with patch('app.main.lib.image_similarity.execute_command') as mock_db_response:
                mock_db_response.return_value = [(1, "1c63abe0-aeb4-4bac-8925-948b69c32d0d", 49805440634311326, 'http://example.com/lenna-512.png', [{'team_id': 1}], 1.0)]
                r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
                r.delete(f"image_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
                r.lpush(f"image_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"body": {"hash_value": 49805440634311326}}))
                mock_response = Mock()
                mock_response.text = json.dumps({
                    'message': 'Message pushed successfully',
                    'queue': 'image__Model',
                    'body': {
                        'callback_url': 'http://alegre:3100/presto/receive/add_item/image',
                        'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                        'url': 'http://example.com/lenna-512.png',
                        'text': None,
                        'raw': {
                            'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                            'url': 'http://example.com/lenna-512.png',
                        }
                    }
                })
                mock_post_request.return_value = mock_response
                response = self.client.post('/similarity/sync/image', data=json.dumps({
                    'url': url,
                    'project_media_id': 1,
                    'context': {
                        'team_id': 1,
                    }
                }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['context', 'doc_id', 'id', 'model', 'phash', 'score', 'url'])
        self.assertEqual(result["result"][0]['url'],'http://example.com/lenna-512.png')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

    def test_video_basic_http_responses_with_doc_id(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        with patch('requests.post') as mock_post_request:
            with patch('app.main.lib.shared_models.video_model.VideoModel.execute_command') as mock_db_response:
                with patch('app.main.lib.shared_models.video_model.tmkpy.query') as mock_query:
                    mock_query.return_value = (1.0,)
                    mock_db_response.return_value = [(1, "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8", 'http://example.com/chair-19-sd-bar.mp4', "f4cf", "78f84604-f4cf-4044-a261-5fdf0ac44b63", [{'team_id': 1}], [-1363.0159912109375, 252.60726928710938, 652.66552734375, 48.47494888305664, -12.226404190063477, -62.87214279174805, -11.51701545715332, -13.31611442565918, -2.3773577213287354, -9.220880508422852, 30.38682746887207, -10.805936813354492, 17.883710861206055])]
                    r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
                    r.delete(f"video_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8")
                    r.lpush(f"video_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8", json.dumps({"body": {"folder": "f4cf", "filepath": "78f84604-f4cf-4044-a261-5fdf0ac44b63", "hash_value": [-1363.0159912109375, 252.60726928710938, 652.66552734375, 48.47494888305664, -12.226404190063477, -62.87214279174805, -11.51701545715332, -13.31611442565918, -2.3773577213287354, -9.220880508422852, 30.38682746887207, -10.805936813354492, 17.883710861206055]}}))
                    mock_response = Mock()
                    mock_response.text = json.dumps({
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
                    mock_post_request.return_value = mock_response
                    response = self.client.post('/similarity/sync/video', data=json.dumps({
                        'url': url,
                        'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8",
                        'context': {
                            'team_id': 1,
                        }
                    }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['context', 'doc_id', 'filename', 'filepath', 'folder', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['doc_id'], 'Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8')
        self.assertEqual(result["result"][0]['url'], 'http://example.com/chair-19-sd-bar.mp4')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

    def test_video_basic_http_responses(self):
        url = 'http://example.com/chair-19-sd-bar.mp4'
        with patch('requests.post') as mock_post_request:
            with patch('app.main.lib.shared_models.video_model.VideoModel.execute_command') as mock_db_response:
                with patch('app.main.lib.shared_models.video_model.tmkpy.query') as mock_query:
                    mock_query.return_value = (1.0,)
                    mock_db_response.return_value = [(1, "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8", 'http://example.com/chair-19-sd-bar.mp4', "f4cf", "78f84604-f4cf-4044-a261-5fdf0ac44b63", [{'team_id': 1}], [-1363.0159912109375, 252.60726928710938, 652.66552734375, 48.47494888305664, -12.226404190063477, -62.87214279174805, -11.51701545715332, -13.31611442565918, -2.3773577213287354, -9.220880508422852, 30.38682746887207, -10.805936813354492, 17.883710861206055])]
                    r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
                    r.delete(f"video_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8")
                    r.lpush(f"video_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8", json.dumps({"body": {"folder": "f4cf", "filepath": "78f84604-f4cf-4044-a261-5fdf0ac44b63", "hash_value": [-1363.0159912109375, 252.60726928710938, 652.66552734375, 48.47494888305664, -12.226404190063477, -62.87214279174805, -11.51701545715332, -13.31611442565918, -2.3773577213287354, -9.220880508422852, 30.38682746887207, -10.805936813354492, 17.883710861206055]}}))
                    mock_response = Mock()
                    mock_response.text = json.dumps({
                        'message': 'Message pushed successfully',
                        'queue': 'video__Model',
                        'body': {
                            'callback_url': 'http://alegre:3100/presto/receive/add_item/video',
                            'id': "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8",
                            'url': 'http://example.com/chair-19-sd-bar.mp4',
                            'text': None,
                            'raw': {
                                'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8",
                                'url': 'http://example.com/chair-19-sd-bar.mp4'
                            }
                        }
                    })
                    mock_post_request.return_value = mock_response
                    response = self.client.post('/similarity/sync/video', data=json.dumps({
                        'url': url,
                        'project_media_id': 1,
                        'context': {
                            'team_id': 1,
                        }
                    }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['context', 'doc_id', 'filename', 'filepath', 'folder', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['url'],'http://example.com/chair-19-sd-bar.mp4')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

if __name__ == '__main__':
    unittest.main()