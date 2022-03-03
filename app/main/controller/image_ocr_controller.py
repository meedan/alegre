from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from google.cloud import vision
import tenacity

from app.main.lib.google_client import get_credentialed_google_client

api = Namespace('ocr', description='ocr operations')
ocr_request = api.model('ocr_request', {
    'url': fields.String(required=True, description='url of image to extract text from'),
})

def _after_log(retry_state):
    app.logger.debug("Retrying text extraction...")
@api.route('/')
class ImageOcrResource(Resource):
    @api.response(200, 'text successfully extracted.')
    @api.doc('Perform text extraction from an image')
    @api.doc(params={'url': 'url of image to extract text from'})

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=0, max=5), stop=tenacity.stop_after_attempt(20), after=_after_log, reraise=True)
    def get(self):
        client = get_credentialed_google_client(vision.ImageAnnotatorClient)

        image = vision.types.Image()
        if(request.args.get('url')):
            image.source.image_uri=request.args.get('url')
        else:
            image.source.image_uri = request.json['url']

        response = client.document_text_detection(image=image)

        if response.error:
            raise Exception("we can not access the URL currently. Please download the content and pass it in")

        texts = response.text_annotations

        if not texts:
            return

        return {
            'text': texts[0].description
        }
