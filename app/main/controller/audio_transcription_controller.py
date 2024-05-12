import os
import json
import requests
import botocore
from botocore.exceptions import BotoCoreError, ClientError
import boto3

from flask import request, current_app as app
from flask_restx import Resource, Namespace, fields

from app.main.lib.error_log import ErrorLog

def safely_handle_transcription_job(callback, jobName, audioUri):
    result = None
    try:
        result = callback(jobName, audioUri)
    except botocore.exceptions.ClientError as error:
        ErrorLog.notify(error)
        result = {
            'error': error.response['Error']['Code'],
            'message': error.response['Error']['Message'],
        }
    except Exception as e:
        ErrorLog.notify(e)
        print("Oops!", repr(e), "occurred.")
        result = {
            'error': repr(e),
        }
    return result

def log_abnormal_failure(response):
    normal_failure = False
    for reason in ["Failed to parse audio file", "must have a speech segment long enough in duration ", "Unsupported audio format", "data in your input media file isn't valid"]:
        if reason in response["TranscriptionJob"]["FailureReason"]:
            normal_failure = True
    if not normal_failure:
        ErrorLog.notify(Exception("[ALEGRE] Transcription job failed!"), {"response": response})
    return normal_failure

def transcription_response_package(response):
    return {
        'job_name': response['TranscriptionJob'].get('TranscriptionJobName'),
        'job_status': response['TranscriptionJob'].get('TranscriptionJobStatus'),
        'language_code': response['TranscriptionJob'].get('LanguageCode')
    }
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

def aws_start_transcription(jobName, audioUri):
    try:
        return transcribe.start_transcription_job(
            TranscriptionJobName=jobName,
            IdentifyLanguage=True,
            Media={
                'MediaFileUri': audioUri
            }
        )
    except (BotoCoreError, ClientError) as e:
        if 'ConflictException' in str(e):
            return transcribe.get_transcription_job(TranscriptionJobName=jobName)
        else:
            raise e

def aws_get_transcription(jobName):
    return transcribe.get_transcription_job(TranscriptionJobName=jobName)

def start_transcription(jobName, audioUri):
    result = None
    response = aws_start_transcription(jobName, audioUri)
    if response['TranscriptionJob']:
        result = {
            'job_name': response['TranscriptionJob']['TranscriptionJobName'],
            'job_status': response['TranscriptionJob']['TranscriptionJobStatus'],
        }
    return result

def get_transcription(jobName, audioUri):
    result = None
    response = aws_get_transcription(jobName)
    if response['TranscriptionJob']:
        result = transcription_response_package(response)
        if result["job_status"] == 'COMPLETED':
            transcriptionUri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
            transcriptionResponse = requests.get(transcriptionUri)
            transcriptionResponseDict = json.loads(transcriptionResponse.text)
            result['transcription'] = transcriptionResponseDict['results']['transcripts'][0]['transcript']
        elif result["job_status"] == "FAILED":
            normal_failure = log_abnormal_failure(response)
            if normal_failure:
                result["job_status"] = "DONE"
        elif result["job_status"] != 'IN_PROGRESS':
            ErrorLog.notify(Exception("[ALEGRE] Transcription job unknown status!"), {"response": response})
    return result

@api.route('/')
class AudioTranscriptionResource(Resource):

    @api.response(200, 'Transcription job successfully started.')
    @api.doc('Start transcription job')
    @api.expect(transcription_post, validate=False)
    def post(self):
        jobName = request.json.get('job_name', '')
        audioUri = request.json.get('url', '')
        return safely_handle_transcription_job(start_transcription, jobName, audioUri)

@api.route('/result/')
class AudioTranscriptionResultResource(Resource):
    @api.response(200, 'OK')
    @api.doc('Get transcription result')
    @api.doc(params={'job_name': 'unique transcription job identifier'})
    def post(self):
        jobName = request.json.get('job_name')
        return safely_handle_transcription_job(get_transcription, jobName, None)
