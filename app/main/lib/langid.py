# 3rd party langid providers
from google.cloud import translate_v2 as translate
from flask import current_app as app
import requests
import cld3

class GoogleLangidProvider:
# https://cloud.google.com/translate/docs/reference/libraries/v2/python
  @staticmethod
  def langid(text):
    client = translate.Client.from_service_account_json('./google_credentials.json')
    response = client.detect_language([text])
    return {
      'result': {
        'language': response[0]['language'],
        'confidence': response[0]['confidence']
      },
      'raw': response
    }

  @staticmethod
  def languages():
    client = translate.Client.from_service_account_json('./google_credentials.json')
    response = client.get_languages()
    return {
      'result': response,
      'raw': response
    }

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
    return {
      'result': {
        'language': 'und' if response['documents'][0]['detectedLanguages'][0]['iso6391Name'] == '(Unknown)' else response['documents'][0]['detectedLanguages'][0]['iso6391Name'],
        'confidence': response['documents'][0]['detectedLanguages'][0]['score']
      },
      'raw': response
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

class Cld3LangidProvider:
# https://github.com/bsolomon1124/pycld3
  @staticmethod
  def langid(text):
    prediction = cld3.get_language(text)
    return {
      'result': {
        'language': prediction.language,
        'confidence': prediction.probability
      },
      'raw': prediction
    }

  @staticmethod
  def languages():
    # FIXME
    return []

  @staticmethod
  def test():
    return True
