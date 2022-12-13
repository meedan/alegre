from flask import request, current_app as app
from flask_restx import Resource, Namespace, fields
import boto3
import botocore
import requests
import json
import os

def safely_handle_transcription_job(callback):
    result = None
    try:
        result = callback()
    except botocore.exceptions.ClientError as error:
        result = {
            'error': error.response['Error']['Code'],
            'message': error.response['Error']['Message'],
        }
    except Exception as e:
        print("Oops!", repr(e), "occurred.")
        result = {
            'error': repr(e),
        }
    return result

api = Namespace('audio_transcription', description='audio transcription operations')
transcription_post = api.model('transcription_post', {
    'url': fields.String(required=True, description='url of audio to transcribe'),
    'job_name': fields.String(required=True, description='unique transcription job identifier'),
})

transcription_get = api.model('transcription_get', {
    'job_name': fields.String(required=True, description='unique transcription job identifier'),
})

transcribe = boto3.client(
    'transcribe',
    os.getenv('AWS_DEFAULT_REGION', 'eu-west-1')
)

@api.route('/')
class AudioTranscriptionResource(Resource):
    def aws_start_transcription(self, jobName, audioUri):
        return transcribe.start_transcription_job(
            TranscriptionJobName=jobName,
            IdentifyLanguage=True,
            Media={
                'MediaFileUri': audioUri
            }
        )

    def aws_get_transcription(self, jobName):
        return transcribe.get_transcription_job(TranscriptionJobName=jobName)

    @api.response(200, 'Transcription job successfully started.')
    @api.doc('Start transcription job')
    @api.expect(transcription_post, validate=False)
    def post(self):
        jobName = request.get_json().get('job_name', '')
        audioUri = request.get_json().get('url', '')
        def start_transcription():
            result = None
            response = self.aws_start_transcription(jobName, audioUri)
            if response['TranscriptionJob']:
                result = {
                    'job_name': response['TranscriptionJob']['TranscriptionJobName'],
                    'job_status': response['TranscriptionJob']['TranscriptionJobStatus'],
                }
            return result
        return safely_handle_transcription_job(start_transcription)

    @api.response(200, 'OK')
    @api.doc('Get transcription result')
    @api.doc(params={'job_name': 'unique transcription job identifier'})
    def get(self):
        jobName = ''
        if (request.args.get('job_name')):
            jobName = request.args.get('job_name')
        else:
            jobName = request.json['job_name']
        def get_transcription():
            result = None
            response = self.aws_get_transcription(jobName)
            if response['TranscriptionJob']:
                job_name = response['TranscriptionJob']['TranscriptionJobName']
                job_status = response['TranscriptionJob']['TranscriptionJobStatus']
                language_code = response['TranscriptionJob']['LanguageCode']
                result = {
                    'job_name': job_name,
                    'job_status': job_status,
                    'language_code': language_code
                }
                if job_status == 'COMPLETED':
                    transcriptionUri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    transcriptionResponse = requests.get(transcriptionUri)
                    transcriptionResponseDict = json.loads(transcriptionResponse.text)
                    result['transcription'] = transcriptionResponseDict['results']['transcripts'][0]['transcript']
            return result
        return safely_handle_transcription_job(get_transcription)
