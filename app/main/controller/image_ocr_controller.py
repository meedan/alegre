from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from google.cloud import vision

from app.main.lib.google_client import get_credentialed_google_client

api = Namespace('ocr', description='ocr operations')
ocr_request = api.model('ocr_request', {
    'url': fields.String(required=True, description='url of image to extract text from'),
})

@api.route('/')
class ImageOcrResource(Resource):
    @api.response(200, 'text successfully extracted.')
    @api.doc('Perform text extraction from an image')
    @api.expect(ocr_request, validate=True)
    def get(self):
        client = get_credentialed_google_client(vision.ImageAnnotatorClient)

        image = vision.types.Image()
        image.source.image_uri = request.json['url']

        response = client.document_text_detection(image=image)
        texts = response.text_annotations

        return {
            'text': texts[0].description
        }