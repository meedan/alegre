# 3rd party langid providers
from google.cloud import translate
from flask import current_app as app
import requests

class GoogleLangidProvider:
    @staticmethod
    def langid(text):
        client = translate.Client.from_service_account_json('./google_credentials.json')
        return client.detect_language([text])[0]

class MicrosoftLangidProvider:
    @staticmethod
    def langid(text):
        # https://docs.microsoft.com/en-us/azure/cognitive-services/Text-Analytics/quickstarts/python
        response = requests.post(
          app.config['MS_TEXT_ANALYTICS_URL'] + '/languages',
          headers={
            "Ocp-Apim-Subscription-Key": app.config['MS_TEXT_ANALYTICS_KEY']
          },
          json={
            "documents": [{ "id": "1", "text": text }]
          }
        ).json()
        result = response['documents'][0]['detectedLanguages'][0]
        return {
          'language': result['iso6391Name'],
          'confidence': result['score']
        }