import json
from flask import request, current_app as app
from urllib3 import Retry
from flask_restplus import Resource, Namespace, fields
from google.cloud import vision
import tenacity

from app.main.lib.google_client import get_credentialed_google_client
from app.main.lib.google_client import convert_text_annotation_to_json

api = Namespace('ocr', description='ocr operations')
ocr_request = api.model('ocr_request', {
    'url': fields.String(required=True, description='url of image to extract text from'),
})

def _after_log(retry_state):
    app.logger.debug("Retrying text extraction...")

CLIENT = get_credentialed_google_client(vision.ImageAnnotatorClient)
@api.route('/')
class ImageOcrResource(Resource):
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
            f"[Alegre OCR] [image_uri {image.source.image_uri}] Image OCR response package looks like {convert_text_annotation_to_json(texts[0])}")

        return {
            'text': texts[0].description
        }
