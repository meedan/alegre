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
  'url': fields.String(required=False, description='image URL to be stored or queried for similarity'),
  'doc_id': fields.String(required=False, description='image ID to constrain uniqueness'),
  'threshold': fields.Float(required=False, default=0.9, description='minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)'),
  'context': JsonObject(required=False, default=[], description='context')
})

def _after_log(retry_state):
  app.logger.debug("Retrying image similarity...")

def delete_record(params):
  deleted= False
  if params.get('doc_id'):
    deleted = db.session.query(ImageModel).filter(ImageModel.doc_id==params['doc_id']).delete()
  if deleted:
    return {'deleted': True}
  else:
    return {'deleted': False}

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
    try:
      if request.json.get("doc_id"):
        delete_record(request.json)
      image = ImageModel.from_url(request.json['url'], request.json.get('doc_id'), request.json['context'])
      self.save(image)
      return {
        'success': True
      }
    except Exception as e:
      db.session.rollback()
      raise e

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
    if 'url' not in request.json:
      result = self.search_by_context(request.json['context'])
    else:
      image = ImageModel.from_url(request.json['url'], None)
      threshold = 0.9
      if 'threshold' in request.json:
        threshold = request.json['threshold']
      result = self.search_by_phash(image.phash, int(round((1.0 - float(threshold)) * 64.0)), request.json['context'])
    return {
      'result': result
    }

  @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
  def search_by_context(self, context):
    try:
      context_query, context_hash = self.get_context_query(context)
      if context_query:
          cmd = """
            SELECT id, sha256, phash, url, context FROM images
            WHERE 
          """+context_query
      else:
          cmd = """
            SELECT id, sha256, phash, url, context FROM images
          """
      matches = db.session.execute(text(cmd), context_hash).fetchall()
      keys = ('id', 'sha256', 'phash', 'url', 'context')
      return [dict(zip(keys, values)) for values in matches]
    except Exception as e:
      db.session.rollback()
      raise e


  def get_context_query(self, context):
    context_query = []
    context_hash = {}
    for key, value in context.items():
      if isinstance(value, list):
        context_clause = "("
        for i,v in enumerate(value):
          context_clause += "context @> '[{\""+key+"\": :context_"+key+"_"+str(i)+"}]'"
          if len(value)-1 != i:
            context_clause += " OR "
          context_hash[f"context_{key}_{i}"] = v
        context_clause += ")"
        context_query.append(context_clause)
      else:
        context_query.append("context @>'[{\""+key+"\": :context_"+key+"}]'")
        context_hash[f"context_{key}"] = value
    return str.join(" AND ",  context_query), context_hash
    
    
  @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
  def search_by_phash(self, phash, threshold, context):
    try:
      context_query, context_hash = self.get_context_query(context)
      if context_query:
          cmd = """
            SELECT * FROM (
              SELECT id, sha256, phash, url, context, BIT_COUNT(phash # :phash)
              AS score FROM images
            ) f
            WHERE score <= :threshold
            AND 
            """+context_query+"""
            ORDER BY score ASC
          """
      else:
          cmd = """
            SELECT * FROM (
              SELECT id, sha256, phash, url, context, BIT_COUNT(phash # :phash)
              AS score FROM images
            ) f
            WHERE score <= :threshold
            ORDER BY score ASC
          """
      matches = db.session.execute(text(cmd), dict(**{
        'phash': phash,
        'threshold': threshold,
      }, **context_hash)).fetchall()
      keys = ('id', 'sha256', 'phash', 'url', 'context', 'score')
      return [dict(zip(keys, values)) for values in matches]
    except Exception as e:
      db.session.rollback()
      raise e
