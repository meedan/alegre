import json
from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from app.main.lib.fields import JsonObject

from app.main.lib import similarity

api = Namespace('image_similarity', description='image similarity operations')
image_similarity_request = api.model('image_similarity_request', {
  'url': fields.String(required=False, description='image URL to be stored or queried for similarity'),
  'doc_id': fields.String(required=False, description='image ID to constrain uniqueness'),
  'threshold': fields.Float(required=False, default=0.9, description='minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)'),
  'context': JsonObject(required=False, default=[], description='context')
})

@api.route('/')
class ImageSimilarityResource(Resource):
      
  @api.response(200, 'image signature successfully deleted from the similarity database.')
  @api.doc('Delete an image signature from the similarity database')
  @api.expect(image_similarity_request, validate=True)
  def delete(self):
    return similarity.delete_item(request.json, "image")

  @api.response(200, 'image signature successfully stored in the similarity database.')
  @api.doc('Store an image signature in the similarity database')
  @api.expect(image_similarity_request, validate=True)
  def post(self):
    return similarity.add_item(request.json, "image")

  def get_from_args_or_json(self, request, key):
    request_json = None
    try:
        request_json = request.json
    except json.decoder.JSONDecodeError:
        request_json = {}
    app.logger.warning(f"Request args are {request.args}")
    value = request.args.get(key) or (request_json and request_json.get(key))
    if key in ["context", "models", "per_model_threshold", "vector"] and value:
      return json.loads(value)
    else:
      return value

  def request_package(self, request):
    return {
      "url": self.get_from_args_or_json(request, 'url'),
      "context": self.get_from_args_or_json(request, 'context'),
      "threshold": self.get_from_args_or_json(request, 'threshold'),
      "limit": (self.get_from_args_or_json(request, 'limit') or similarity.DEFAULT_SEARCH_LIMIT),
    }

  @api.response(200, 'image similarity successfully queried.')
  @api.doc('Make a image similarity query. Note that we currently require GET requests with a JSON body rather than embedded params in the URL. You can achieve this via curl -X GET -H "Content-type: application/json" -H "Accept: application/json" -d \'{"url":"http://some.link/video.mp4", "threshold": 0.5}\' "http://[ALEGRE_HOST]/image/similarity"')
  @api.doc(params={'url': 'image URL to be stored or queried for similarity', 'threshold': 'minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)', 'context': 'context'})
  def get(self):
    return similarity.get_similar_items(self.request_package(request), "image")
