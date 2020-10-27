import json
from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from app.main import db
from app.main.model.image import ImageModel
from app.main.lib.fields import JsonObject
from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound
import tenacity
import pytesseract
from PIL import Image

api = Namespace('image_ocr_controller', description='image to text operations')
image_ocr_request = api.model('image_ocr_request', {
  'url': fields.String(required=True, description='image URL to be stored or queried for OCR'),
  'context': JsonObject(required=False, default=[], description='context')
})

def _after_log(retry_state):
  app.logger.debug("Retrying image OCR...")

@api.route('image/ocr/')
class ImageSimilarityResource(Resource):
  @api.response(200, 'image signature successfully stored in the OCR database.')
  @api.doc('Store an image signature in the OCR database')
  @api.expect(image_ocr_request, validate=True)
  def post(self):
    image = ImageModel.from_url(request.json['url'], request.json['context'])
    
    text = {'data':pytesseract.image_to_string(Image.open(image))}
    print(text)
    
    return json.dumps(text)
