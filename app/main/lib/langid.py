# 3rd party langid providers
from google.cloud import translate_v2 as translate
from flask import current_app as app
import requests

class GoogleLangidProvider:
# https://cloud.google.com/translate/docs/reference/libraries/v2/python
  @staticmethod
  def langid(text):
    client = translate.Client.from_service_account_json('./google_credentials.json')
    return client.detect_language([text])[0]

  @staticmethod
  def languages():
    client = translate.Client.from_service_account_json('./google_credentials.json')
    return client.get_languages()

  @staticmethod
  def test():
    GoogleLangidProvider.languages()
    return True


class MicrosoftLangidProvider:
# https://docs.microsoft.com/en-us/azure/cognitive-services/Text-Analytics/quickstarts/python
  @staticmethod
  def langid(text):
    response = requests.post(
      app.config['MS_TEXT_ANALYTICS_URL'] + '/languages',
      headers={
        'Ocp-Apim-Subscription-Key': app.config['MS_TEXT_ANALYTICS_KEY']
      },
      json={
        'documents': [{ 'id': '1', 'text': text }]
      }
    ).json()
    if 'error' in response:
      raise Exception(response['error'])
    result = response['documents'][0]['detectedLanguages'][0]
    return {
      'language': result['iso6391Name'],
      'confidence': result['score']
    }

  @staticmethod
  def languages():
    # FIXME https://docs.microsoft.com/en-us/azure/cognitive-services/text-analytics/language-support
    return []

  @staticmethod
  def test():
    # FIXME Find a better way to test proper config
    MicrosoftLangidProvider.langid('hello, world')
    return True
