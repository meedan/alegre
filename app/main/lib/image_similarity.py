from flask import current_app as app
from app.main import db
from app.main.model.image import ImageModel
from app.main.lib.helpers import context_matches
from app.main.lib.similarity_helpers import get_context_query
from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound
import tenacity

def _after_log(retry_state):
  app.logger.debug("Retrying image similarity...")

def delete_image(params):
  deleted= False
  if params.get('doc_id'):
    deleted = db.session.query(ImageModel).filter(ImageModel.doc_id==params['doc_id']).delete()
  if deleted:
    return {'deleted': True}
  else:
    return {'deleted': False}

@tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
def save(image):
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

def add_image(save_params):
  try:
    if save_params.get("doc_id"):
      delete_image(save_params)
    image = ImageModel.from_url(save_params['url'], save_params.get('doc_id'), save_params['context'], save_params.get("created_at"))
    save(image)
    return {
      'success': True
    }
  except Exception as e:
    db.session.rollback()
    raise e

def search_image(params):
  url = params.get("url")
  context = params.get("context")
  threshold = params.get("threshold")
  if not context:
    context = {}
  if not threshold:
    threshold = 0.9
  if url:
    image = ImageModel.from_url(url, None)
    result = search_by_phash(image.phash, int(round((1.0 - float(threshold)) * 64.0)), context)
  else:
    result = search_by_context(context)
  return {
    'result': result
  }

@tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
def search_by_context(context):
  try:
    context_query, context_hash = get_context_query(context)
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
    rows = [dict(zip(keys, values)) for values in matches]
    for row in rows:
      row["context"] = [c for c in row["context"] if context_matches(context, c)]
    return rows
  except Exception as e:
    db.session.rollback()
    raise e  
  
@tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
def search_by_phash(phash, threshold, context):
  try:
    context_query, context_hash = get_context_query(context)
    if context_query:
        cmd = """
          SELECT * FROM (
            SELECT id, sha256, phash, url, context, bit_count_image(phash # :phash)
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
            SELECT id, sha256, phash, url, context, bit_count_image(phash # :phash)
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