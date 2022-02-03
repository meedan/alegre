import unittest
import json

from flask import current_app as app
from unittest.mock import patch
from app.main import db
from app.test.base import BaseTestCase
from unittest import mock

class TestTranscriptionBlueprint(BaseTestCase):
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


if __name__ == '__main__':
    unittest.main()
