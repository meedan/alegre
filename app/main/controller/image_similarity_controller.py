import json
from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from app.main.lib.fields import JsonObject
from app.main.lib.image_similarity import save_image, search_image

api = Namespace('image_similarity', description='image similarity operations')
image_similarity_request = api.model('image_similarity_request', {
  'url': fields.String(required=False, description='image URL to be stored or queried for similarity'),
  'doc_id': fields.String(required=False, description='image ID to constrain uniqueness'),
  'threshold': fields.Float(required=False, default=0.9, description='minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)'),
  'context': JsonObject(required=False, default=[], description='context')
})

@api.route('/')
class ImageSimilarityResource(Resource):
      
  # @api.response(200, 'image signature successfully stored in the similarity database.')
  # @api.doc('Store an image signature in the similarity database')
  # def delete(self):
  #     return delete_record(request.json)

  @api.response(200, 'image signature successfully stored in the similarity database.')
  @api.doc('Store an image signature in the similarity database')
  @api.expect(image_similarity_request, validate=True)
  def post(self):
    return save_image(request.json)

  def get_from_args_or_json(self, request, key):
    return request.args.get(key) or (request.json and request.json.get(key))

  @api.response(200, 'image similarity successfully queried.')
  @api.doc('Make an image similarity query')
  @api.expect(image_similarity_request, validate=False)
  def get(self):
    return search_image(
      self.get_from_args_or_json(request, 'url'),
      self.get_from_args_or_json(request, 'context'),
      self.get_from_args_or_json(request, 'threshold'),
    )

