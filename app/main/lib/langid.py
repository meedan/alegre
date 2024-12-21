# 3rd party langid providers
from flask import current_app as app
import json

from google.cloud import translate_v2 as translate
# import requests # Used for MicrosoftLangidProvider
import cld3
import fasttext


from app.main.lib.google_client import get_credentialed_google_client

class GoogleLangidProvider:
# https://cloud.google.com/translate/docs/reference/libraries/v2/python
  @staticmethod
  def langid(text):
    client = get_credentialed_google_client(translate.Client)
    response = client.detect_language([text])
    return {
      'result': {
        'language': response[0]['language'],
        'confidence': response[0]['confidence']
      },
      'raw': response,
      'model': 'Google',
    }

  @staticmethod
  def languages():
    client = get_credentialed_google_client(translate.Client)
    response = client.get_languages()
    return {
      'result': response,
      'raw': response
    }

  @staticmethod
  def test():
    GoogleLangidProvider.languages()
    return True


# class MicrosoftLangidProvider:
# # https://docs.microsoft.com/en-us/azure/cognitive-services/Text-Analytics/quickstarts/python
#   @staticmethod
#   def langid(text):
#     response = requests.post(
#       app.config['MS_TEXT_ANALYTICS_URL'] + '/languages',
#       headers={
#         'Ocp-Apim-Subscription-Key': app.config['MS_TEXT_ANALYTICS_KEY']
#       },
#       json={
#         'documents': [{ 'id': '1', 'text': text }]
#       }
#     ).json()
#     if 'error' in response:
#       raise Exception(response['error'])
#     return {
#       'result': {
#         'language': 'und' if response['documents'][0]['detectedLanguages'][0]['iso6391Name'] == '(Unknown)' else response['documents'][0]['detectedLanguages'][0]['iso6391Name'],
#         'confidence': response['documents'][0]['detectedLanguages'][0]['score']
#       },
#       'raw': response
#     }
#
class Cld3LangidProvider:
# https://github.com/bsolomon1124/pycld3
  @staticmethod
  def langid(text):
    prediction = cld3.get_language(text)
    return {
      'result': {
        'language': prediction and prediction.language,
        'confidence': prediction and prediction.probability
      },
      'raw': prediction,
      'model': 'CLD3',
    }

  @staticmethod
  def test():
    cld3.get_language("Some text to check")
    return True

class FastTextLangidProvider:
# https://fasttext.cc/docs/en/language-identification.html
  fasttext_model = fasttext.load_model("extra/fasttext_language_id/lid.176.ftz")
  @staticmethod
  def langid(text):
    prediction = list(FastTextLangidProvider.fasttext_model.predict(text.replace("\n"," ")))
    # prediction is a list of tuples, e.g., [('__label__en',), array([0.22517213])]

    language = prediction[0][0].split("__")[-1]
    prediction[1] = prediction[1].tolist()

    # Use 'fil' for Filipino rather than tl for Tagalog
    if language == "tl":
      language = "fil"

    return {
      'result': {
        'language': language,
        'confidence': prediction[1][0]
      },
      'raw': prediction,
      'model': 'FastText',
    }

  @staticmethod
  def test():
    FastTextLangidProvider.fasttext_model.get_language("Some text to check")
    return True

class HybridLangidProvider:
  @staticmethod
  def langid(text):
    fasttext_result = FastTextLangidProvider.langid(text)
    cld_result = Cld3LangidProvider.langid(text)
    # max_confidence = max(fasttext_result['result']['confidence'], cld_result['result']['confidence'])
    min_confidence = min(fasttext_result['result']['confidence'], cld_result['result']['confidence'])

    # if fasttext_result['result']['language'] == cld_result['result']['language'] or max_confidence >= 0.8:
    if fasttext_result['result']['language'] == cld_result['result']['language'] and min_confidence >= 0.7:
      # OLD - FastText and CLD agree or one of them is more than 80% confident.
      # Now - FastText and CLD agree AND BOTH are more than 90% confident
      # Return the higher confidence result
      # if fasttext_result['result']['language'] != cld_result['result']['language']:
      #   # Log when there is disagreement
      #   app.logger.info(json.dumps({
      #     'service':'LangId',
      #     'message': 'Disagreement between fasttext and cld. Returning higher confidence model',
      #     'parameters':{'text':text, 'fasttext':fasttext_result, 'cld':cld_result,},
      #     }))
      if fasttext_result['result']['confidence'] > cld_result['result']['confidence']:
        return fasttext_result
      else:
        return cld_result
    else:
      # Fallback to Google when models disagree and neither has a high-confidence result
      google_result = GoogleLangidProvider.langid(text)
      app.logger.info(json.dumps({
        'service':'LangId',
        'message': 'Called Google after inconclusive local results',
        'parameters':{'text':text, 'fasttext':fasttext_result, 'cld':cld_result, 'google':google_result},
        }))
      return google_result

  @staticmethod
  def test():
    HybridLangidProvider.langid("Some text to check")
    return True
