import json
from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from app.main import db
from app.main.model.image import ImageModel
from app.main.lib.fields import JsonObject
from sqlalchemy import text

api = Namespace('image_similarity', description='image similarity operations')
image_similarity_request = api.model('image_similarity_request', {
  'url': fields.String(required=True, description='image URL to be stored or queried for similarity'),
  'threshold': fields.Float(required=False, default=1.0, description='minimum score to consider, between 0 and 64 (defaults to 1)'),
  'context': JsonObject(required=False, description='context')
})

@api.route('/')
class ImageSimilarityResource(Resource):
  @api.response(200, 'image signature successfully stored in the similarity database.')
  @api.doc('Store an image signature in the similarity database')
  @api.expect(image_similarity_request, validate=True)
  def post(self):
    result = True
    image = ImageModel.from_url(request.json['url'], request.json['context'])
    db.session.add(image)
    db.session.commit()
    db.session.flush()

    return {
      'success': result
    }

  @api.response(200, 'image similarity successfully queried.')
  @api.doc('Make an image similarity query')
  @api.expect(image_similarity_request, validate=True)
  def get(self):
    image = ImageModel.from_url(request.json['url'], {})
    result = self.search_by_phash(image.phash, request.json['threshold'], request.json['context'], 1, 0)
    return {
      'result': result
    }

  def search_by_phash(self, phash, threshold, filter, limit, offset):
    cmd = """
      SELECT * FROM (
        SELECT images.*, BIT_COUNT(phash # :phash)
        AS score FROM images
      ) f
      WHERE score <= :threshold
      AND context @> (:filter)::jsonb
      ORDER BY score ASC
      LIMIT :limit
      OFFSET :offset
    """
    matches = db.session.execute(text(cmd), {
      'phash': phash,
      'threshold': threshold,
      'filter': json.dumps(filter),
      'limit': limit,
      'offset': offset
    }).fetchall()
    keys = ('id', 'sha256', 'phash', 'url', 'context', 'score')
    results = [ dict(zip(keys, values)) for values in matches ]
    return results
