# 3rd party image classification providers
from google.cloud import vision
from protobuf_to_dict import protobuf_to_dict

class GoogleImageClassificationProvider:
    @staticmethod
    def classify(uri):
        client = vision.ImageAnnotatorClient.from_service_account_json('./google_credentials.json')
        response = client.annotate_image({
          'image': {'source': {'image_uri': uri}},
          'features': [
            {'type': vision.enums.Feature.Type.SAFE_SEARCH_DETECTION},
            {'type': vision.enums.Feature.Type.LABEL_DETECTION}
          ]
        })
        raw = protobuf_to_dict(response)
        return {
          'result': {
            'flags': {**raw['safe_search_annotation'], 'spam': vision.enums.Likelihood.UNKNOWN}
          },
          'raw': raw
        }
