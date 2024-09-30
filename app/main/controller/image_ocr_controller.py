import json
from flask import request, current_app as app
from urllib3 import Retry
from flask_restplus import Resource, Namespace, fields
from google.cloud import vision
import tenacity

from app.main.lib.google_client import get_credentialed_google_client, convert_text_annotation_to_json

api = Namespace('ocr', description='ocr operations')
ocr_request = api.model('ocr_request', {
    'url': fields.String(required=True, description='url of image to extract text from'),
})

def _after_log(retry_state):
    app.logger.debug("Retrying text extraction...")

CLIENT = get_credentialed_google_client(vision.ImageAnnotatorClient)
@api.route('/')
class ImageOcrResource(Resource):
    def polygon_area(self, vertices):
        area = 0
        for i in range(len(vertices)):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % len(vertices)]
            area += (x1 * y2 - x2 * y1)
        return abs(area) / 2
    def calculate_text_percentage(self, response):
        bounds = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                    bounds.append(block.bounding_box)
        total_text_area = 0
        for annotation in bounds:
            vertices = [(v.x, v.y) for v in annotation.vertices]
            area = self.polygon_area(vertices)
            total_text_area += area
        # response object contains the whole image width and height in response.full_text_annotation.pages[0]
        # as we are sending images, response.full_text_annotation.pages is always 1 page only
        image_area = response.full_text_annotation.pages[0].width * response.full_text_annotation.pages[0].height
        text_percentage = (total_text_area / image_area) * 100
        return text_percentage

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

        #### calculate bounding boxes areas.
        try:
            text_percentage = self.calculate_text_percentage(response)
            app.logger.info(
                f"[Alegre OCR] [image_uri {image.source.image_uri}] [percentage of image area covered by text {text_percentage}%] Image OCR response package looks like {convert_text_annotation_to_json(texts[0])}")
        except Exception as caught_exception:
            app.logger.error(f"[image_uri {image.source.image_uri}] Error calculating percentage of image area covered by text. Error was {caught_exception}. Image OCR response package looks like {convert_text_annotation_to_json(texts[0])}")

        # Assuming the image has a known width and height (you'll need to replace this with your actual image dimensions)
        image_width = response.full_text_annotation.pages[0].width
        image_height = response.full_text_annotation.pages[0].height
        return {
            'text': texts[0].description
        }
