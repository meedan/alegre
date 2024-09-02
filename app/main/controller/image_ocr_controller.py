from flask import request, current_app as app
from urllib3 import Retry
from flask_restplus import Resource, Namespace, fields
from google.cloud import vision
import tenacity
import json

from app.main.lib.google_client import get_credentialed_google_client

api = Namespace('ocr', description='ocr operations')
ocr_request = api.model('ocr_request', {
    'url': fields.String(required=True, description='url of image to extract text from'),
})

def _after_log(retry_state):
    app.logger.debug("Retrying text extraction...")

CLIENT = get_credentialed_google_client(vision.ImageAnnotatorClient)
@api.route('/')
class ImageOcrResource(Resource):
    def convert_text_annotation_to_json(self, text_annotation):
        text_json = {}
        text_json['description'] = text_annotation.description
        text_json['locale'] = text_annotation.locale
        text_json['bounding_poly'] = []
        for a_vertice in text_annotation.bounding_poly.vertices:
            vertice_json = {}
            vertice_json['x'] = a_vertice.x
            vertice_json['y'] = a_vertice.y
            text_json['bounding_poly'] += [vertice_json]
        text_json = json.dumps(text_json)
        return text_json

    @api.response(200, 'text successfully extracted.')
    @api.doc('Perform text extraction from an image')
    @api.doc(params={'url': 'url of image to extract text from'})
    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=2, max=5), stop=(tenacity.stop_after_attempt(3) | tenacity.stop_after_delay(10)), after=_after_log, reraise=True)
    def post(self):
        image = vision.types.Image()
        image.source.image_uri = request.json['url']

        response = CLIENT.document_text_detection(image=image)

        if response.error.message:
            raise Exception(response.error.message)

        texts = response.text_annotations

        if not texts:
            return

        app.logger.info(
            f"[Alegre OCR] [image_uri {image.source.image_uri}] Image OCR response package looks like {self.convert_text_annotation_to_json(texts[0])}")

        return {
            'text': texts[0].description
        }
