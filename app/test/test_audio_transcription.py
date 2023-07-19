import unittest
import json

from flask import current_app as app
from unittest.mock import patch
from app.main import db
from app.test.base import BaseTestCase
from unittest import mock
from collections import namedtuple
from botocore.exceptions import ClientError
from app.main.controller.audio_transcription_controller import log_abnormal_failure, transcription_response_package
class TestTranscriptionBlueprint(BaseTestCase):
    def test_log_abnormal_failure_returns_true(self):
        self.assertEqual(True, log_abnormal_failure({"TranscriptionJob": {"FailureReason": "Failed to parse audio file."}}))
        
    def test_log_abnormal_failure_returns_false(self):
        with patch("app.main.lib.error_log.ErrorLog.notify") as mock_notify:
            mock_notify.return_value = True
            self.assertEqual(False, log_abnormal_failure({"TranscriptionJob": {"FailureReason": "some other problem"}}))

    
    def test_transcription_response_package(self):
        self.assertEqual({'job_name': "foo", 'job_status': "bar", 'language_code': "baz"}, transcription_response_package({"TranscriptionJob": {"TranscriptionJobName": "foo", "TranscriptionJobStatus": "bar", "LanguageCode": "baz"}}))

    def test_post_transcription_job(self):
        with patch('app.main.controller.audio_transcription_controller.AudioTranscriptionResource.aws_start_transcription', ) as mock_start_transcription:
            mock_start_transcription.return_value = {
                'TranscriptionJob': {
                    'TranscriptionJobName': 'Aloha',
                    'TranscriptionJobStatus': 'IN_PROGRESS',
                }
            }
            response = self.client.post('/audio/transcription/',
                data=json.dumps({
                  'url': 's3://hello-audio-transcription/en-01.wav',
                  'job_name': 'Aloha',
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual('application/json', response.content_type)
            self.assertEqual(200, response.status_code)
            self.assertEqual(sorted(result.keys()), ['job_name', 'job_status'])

    def test_get_transcription_job(self):
        with patch('app.main.controller.audio_transcription_controller.AudioTranscriptionResource.aws_get_transcription', ) as mock_get_transcription:
            mock_get_transcription.return_value = {
                'TranscriptionJob': {
                    'TranscriptionJobName': 'Aloha',
                    'TranscriptionJobStatus': 'IN_PROGRESS',
                    'LanguageCode': 'en-EN',
                }
            }
            response = self.client.get('/audio/transcription/',
                data=json.dumps({
                  'job_name': 'Aloha',
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual('application/json', response.content_type)
            self.assertEqual(200, response.status_code)
            self.assertEqual(sorted(result.keys()), ['job_name', 'job_status', 'language_code'])

    def test_get_transcription_job_with_query_request(self):
        with patch('app.main.controller.audio_transcription_controller.AudioTranscriptionResource.aws_get_transcription', ) as mock_get_transcription:
            mock_get_transcription.return_value = {
                'TranscriptionJob': {
                    'TranscriptionJobName': 'Aloha',
                    'TranscriptionJobStatus': 'IN_PROGRESS',
                    'LanguageCode': 'en-EN',
                }
            }
            response = self.client.get('/audio/transcription/?job_name=Aloha')
            result = json.loads(response.data.decode())
            self.assertEqual('application/json', response.content_type)
            self.assertEqual(200, response.status_code)
            self.assertEqual(sorted(result.keys()), ['job_name', 'job_status', 'language_code'])

    def test_get_completed_transcription_job(self):
        with patch('app.main.controller.audio_transcription_controller.AudioTranscriptionResource.aws_get_transcription', ) as mock_get_transcription:
            with patch('requests.get') as requests:
                url = 'file:///app/app/test/data/test_audio_1.mp3'
                mock_get_transcription.return_value = {
                    'TranscriptionJob': {
                        'TranscriptionJobName': 'Aloha',
                        'TranscriptionJobStatus': 'COMPLETED',
                        'LanguageCode': 'en-EN',
                        'Transcript': {'TranscriptFileUri': url}
                    }
                }
                transcription_text = """{"jobName":"audiot","accountId":"848416313321","results":{"language_code":"pt-BR","transcripts":[{"transcript":"a tragédia da"}]}}"""
                struct_helper = namedtuple('struct_helper', 'text')
                requests.return_value = struct_helper(text = transcription_text)
                response = self.client.get('/audio/transcription/',
                    data=json.dumps({
                    'job_name': 'Aloha',
                    }),
                    content_type='application/json'
                )
                result = json.loads(response.data.decode())
                self.assertEqual('application/json', response.content_type)
                self.assertEqual(200, response.status_code)
                self.assertEqual(sorted(result.keys()), ['job_name', 'job_status', 'language_code', 'transcription'])

    def test_get_transcription_job_error(self):
        with patch('app.main.controller.audio_transcription_controller.AudioTranscriptionResource.aws_get_transcription', ) as mock_get_transcription:
            mock_get_transcription.return_value = {}
            response = self.client.get('/audio/transcription/',
                data=json.dumps({
                  'job_name': 'Aloha',
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual('application/json', response.content_type)
            self.assertNotEqual(sorted(result.keys()), ['job_name', 'job_status', 'language_code'])
            self.assertTrue('KeyError' in result['error'])

    def test_handle_bot3_exception(self):
        with patch('botocore.client.BaseClient._make_api_call', side_effect= ClientError({'Error': {'Message': 'Duplicated file', 'Code': 'TypeAlreadyExistsFault'}}, 'test-op')):
            response = self.client.get('/audio/transcription/',
                data=json.dumps({
                  'job_name': 'Aloha',
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual('application/json', response.content_type)
            self.assertNotEqual(sorted(result.keys()), ['job_name', 'job_status', 'language_code'])
            self.assertIn('error', result)

    def test_post_transcription_job_with_boto_client(self):
        with patch('botocore.client.BaseClient._make_api_call'):
            response = self.client.post('/audio/transcription/',
                data=json.dumps({
                  'url': 's3://hello-audio-transcription/en-01.wav',
                  'job_name': 'Aloha',
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual('application/json', response.content_type)
            self.assertEqual(200, response.status_code)
            self.assertEqual(sorted(result.keys()), ['job_name', 'job_status'])
            self.assertEqual(None, result['job_name'])
            self.assertEqual(None, result['job_status'])

if __name__ == '__main__':
    unittest.main()
