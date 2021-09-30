from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
import boto3
import requests
import json

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
    'eu-west-1',
)

@api.route('/')
class AudioTranscriptionResource(Resource):
    @api.response(200, 'Transcription job successfully started.')
    @api.doc('Start transcription job')
    @api.expect(transcription_post, validate=False)
    def post(self):
        jobName = request.get_json().get('job_name', '')
        audioUri = request.get_json().get('url', '')
        result = None

        # try:
        response = transcribe.start_transcription_job(
        TranscriptionJobName=jobName,
            IdentifyLanguage=True,
            Media={
                'MediaFileUri': audioUri
            }
        )

        if response['TranscriptionJob']:
            result = {
                'job_name': response['TranscriptionJob']['TranscriptionJobName'],
                'job_status': response['TranscriptionJob']['TranscriptionJobStatus'],
            }

        # except Exception as e:
        # 	print("Oops!", e.__class__, "occurred.")
        # 	result = {
        # 		'error': e.__class__,
        # 	}

        return result

    @api.response(200, 'OK')
    @api.doc('Get transcription result')
    @api.expect(transcription_get, validate=False)
    def get(self):
        jobName = ''

        if (request.args.get('job_name')):
            jobName = request.args.get('job_name')
        else:
            jobName = request.json['job_name']

        result = None

        # try:
        response = transcribe.get_transcription_job(TranscriptionJobName=jobName)

        if response['TranscriptionJob']:
            job_name = response['TranscriptionJob']['TranscriptionJobName']
            job_status = response['TranscriptionJob']['TranscriptionJobStatus']

            result = {
                'job_name': job_name,
                'job_status': job_status,
            }

            if job_status == 'COMPLETED':
                transcriptionUri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                transcriptionResponse = requests.get(transcriptionUri)
                transcriptionResponseDict = json.loads(transcriptionResponse.text)
                result['transcription'] = transcriptionResponseDict['results']['transcripts'][0]['transcript']

        # except Exception as e:
        #     print("Oops!", e.__class__, "occurred.")
        #     result = {
        #         'error': e.__class__,
        #     }

        return result
