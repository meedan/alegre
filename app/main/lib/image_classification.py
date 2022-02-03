# 3rd party image classification providers
from google.cloud import vision
from protobuf_to_dict import protobuf_to_dict
from flask import request, current_app as app

from app.main.lib.google_client import get_credentialed_google_client

CLIENT = get_credentialed_google_client(vision.ImageAnnotatorClient)

class GoogleImageClassificationProvider:
    @staticmethod
    def classify(uri):
        print("in classify...")
        if CLIENT == None:
          raise "Client not credentialed, can't use google image classification."
        response = CLIENT.annotate_image({
          'image': {'source': {'image_uri': uri}},
          'features': [
            {'type': vision.enums.Feature.Type.SAFE_SEARCH_DETECTION},
            {'type': vision.enums.Feature.Type.LABEL_DETECTION}
          ]
        })
        if response.error.message:
          raise Exception(response.error.message)
        raw = protobuf_to_dict(response)
        return {
          'result': {
            'flags': {**raw['safe_search_annotation'], 'spam': vision.enums.Likelihood.UNKNOWN}
          },
          'raw': raw
        }
