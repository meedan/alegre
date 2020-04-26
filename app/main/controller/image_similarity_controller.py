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

api = Namespace('image_similarity', description='image similarity operations')
image_similarity_request = api.model('image_similarity_request', {
  'url': fields.String(required=True, description='image URL to be stored or queried for similarity'),
  'threshold': fields.Float(required=False, default=0.9, description='minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)'),
  'context': JsonObject(required=False, default=[], description='context')
})

def _after_log(retry_state):
    app.logger.debug("Retrying image similarity...")

@api.route('/')
class ImageSimilarityResource(Resource):
  @api.response(200, 'image signature successfully stored in the similarity database.')
  @api.doc('Store an image signature in the similarity database')
  @api.expect(image_similarity_request, validate=True)
  def post(self):
    image = ImageModel.from_url(request.json['url'], request.json['context'])
    self.save(image)
    return {
      'success': True
    }

  @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
  def save(self, image):
    try:
      # First locate existing image and append new context
      existing = db.session.query(ImageModel).filter(ImageModel.url==image.url).one()
      existing.context.append(image.context)
      flag_modified(existing, 'context')
    except NoResultFound as e:
      # Otherwise, add new image, but with context as an array
      if image.context:
        image.context = [image.context]
      db.session.add(image)
    except Exception as e:
      db.session.rollback()
      raise e

    try:
      db.session.commit()
    except Exception as e:
      db.session.rollback()
      raise e

  @api.response(200, 'image similarity successfully queried.')
  @api.doc('Make an image similarity query')
  @api.expect(image_similarity_request, validate=False)
  def get(self):
    try:
      if 'url' not in request.json:
        result = self.search_by_context(request.json['context'])
      else:
        image = ImageModel.from_url(request.json['url'])
        threshold = 0.9
        if 'threshold' in request.json:
          threshold = request.json['threshold']
        result = self.search_by_phash(image.phash, int(round((1.0 - float(threshold)) * 64.0)), request.json['context'])
      return {
        'result': result
      }
    except Exception as e:
      db.session.rollback()
      raise e

  def search_by_context(self, context):
    cmd = """
      SELECT * FROM images
      WHERE context @> (:context)::jsonb
    """
    matches = db.session.execute(text(cmd), {
      'context': json.dumps([context])
    }).fetchall()
    keys = ('id', 'sha256', 'phash', 'url', 'context')
    results = [ dict(zip(keys, values)) for values in matches ]
    return results

  def search_by_phash(self, phash, threshold, context):
    cmd = """
      SELECT * FROM (
        SELECT images.*, BIT_COUNT(phash # :phash)
        AS score FROM images
      ) f
      WHERE score <= :threshold
      AND context @> (:context)::jsonb
      ORDER BY score ASC
    """
    matches = db.session.execute(text(cmd), {
      'phash': phash,
      'threshold': threshold,
      'context': json.dumps([context])
    }).fetchall()
    keys = ('id', 'sha256', 'phash', 'url', 'context', 'score')
    results = [ dict(zip(keys, values)) for values in matches ]
    return results
