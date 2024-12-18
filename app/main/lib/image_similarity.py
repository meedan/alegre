from flask import current_app as app
from app.main import db
from app.main.model.image import ImageModel
from app.main.lib.helpers import context_matches
from app.main.lib.similarity_helpers import get_context_query, drop_context_from_record
from app.main.lib import media_crud
from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound
import tenacity

def _after_log(retry_state):
  app.logger.debug("Retrying image similarity...")

def delete_image(params):
  deleted = False
  if params.get('doc_id'):
    image = db.session.query(ImageModel).filter(ImageModel.doc_id==params['doc_id']).one_or_none()
    if image:
      if params.get("context", {}) in image.context and len(image.context) > 1:
        deleted = drop_context_from_record(image, params.get("context", {}))
      else:
        deleted = db.session.query(ImageModel).filter(ImageModel.id==image.id).delete()
    db.session.commit()
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

def callback_add_image(task):
    return media_crud.add(task, ImageModel, ["pdq", "phash"])[0]

def search_image(image, model, limit, threshold, task, hash_value, context, temporary):
    if image:
        if model and model.lower() == "pdq":
            image.pdq = hash_value
            result = search_by_pdq(image.pdq, threshold, context, limit)
        else:
            image.phash = hash_value
            result = search_by_phash(image.phash, threshold, context, limit)
        if temporary:
            media_crud.delete(task, ImageModel)
        else:
            media_crud.save(image, ImageModel, ["pdq", "phash"])
        if limit:
            return {"result": result[:limit]}
        else:
            return {"result": result}
    else:
        return {"error": "Image not found for provided task", "task": task}

def blocking_search_image(task):
    image, temporary, context, presto_result = media_crud.get_blocked_presto_response(task, ImageModel, "image")
    threshold = task.get("threshold", 0.0)
    limit = task.get("limit", 200)
    model = app.config['IMAGE_MODEL']
    hash_value = presto_result["body"]["hash_value"]
    return search_image(image, model, limit, threshold, task, hash_value, context, temporary)

def async_search_image(task, modality):
    return media_crud.get_async_presto_response(task, ImageModel, modality)

def async_search_image_on_callback(task):
    if list(task.keys()) == ["raw"]:
        image = media_crud.get_by_doc_id_or_url(task["raw"], ImageModel)
    else:
        image = media_crud.get_by_doc_id_or_url(task, ImageModel)
    model = app.config['IMAGE_MODEL']
    threshold = task.get("raw", {}).get("threshold", 0.0)
    limit = task.get("raw", {}).get("limit", 200)
    context = task.get("raw", {}).get("context", {})
    hash_value = task.get("result", {}).get("hash_value", getattr(image, app.config["IMAGE_MODEL"]))
    return search_image(image, model, limit, threshold, task, hash_value, context, False)

@tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
def search_by_context(context, limit=None):
  try:
    context_query, context_hash = get_context_query(context, False)
    if context_query:
      cmd = """
          SELECT id, doc_id, phash, url, context FROM images
          WHERE 
        """+context_query
    else:
      cmd = """
          SELECT id, doc_id, phash, url, context FROM images
        """
    if limit:
        cmd = cmd+" LIMIT :limit"
    matches = execute_command(text(cmd), dict(**context_hash, **{'limit': limit}))
    keys = ('id', 'doc_id', 'phash', 'url', 'context')
    rows = [dict(zip(keys, values)) for values in matches]
    for row in rows:
      row["context"] = [c for c in row["context"] if context_matches(context, c)]
      row["model"] = "image/context"
    return rows
  except Exception as e:
    db.session.rollback()
    raise e  

def execute_command(cmd, params):
  return db.session.execute(cmd, params).fetchall()

@tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
def search_by_phash(phash, threshold, context, limit=None):
  try:
    context_query, context_hash = get_context_query(context, False) # Changed Since 4126 PR
    if context_query:
        cmd = """
          SELECT * FROM (
            SELECT id, doc_id, phash, url, context, bit_count_image(phash # :phash)
            AS score FROM images
          ) f
          WHERE score >= :threshold
          AND 
          """+context_query+"""
          ORDER BY score DESC
        """
    else:
        cmd = """
          SELECT * FROM (
            SELECT id, doc_id, phash, url, context, bit_count_image(phash # :phash)
            AS score FROM images
          ) f
          WHERE score >= :threshold
          ORDER BY score DESC
        """
    if limit:
        cmd = cmd+" LIMIT :limit"
    matches = execute_command(text(cmd), dict(**{
      'phash': phash,
      'threshold': threshold,
      'limit': limit,
    }, **context_hash))
    keys = ('id', 'doc_id', 'phash', 'url', 'context', 'score')
    rows = []
    for values in matches:
      row = dict(zip(keys, values))
      row["model"] = "image/phash"
      rows.append(row)
    return rows
  except Exception as e:
    db.session.rollback()
    raise e


@tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
def search_by_pdq(pdq, threshold, context, limit=None):
  #bit_count_pdq is defined in mangage.py. It returns a normalized hamming distance between 0 and 1
  #1 represents the strongest similarity possibile.
  try:
    context_query, context_hash = get_context_query(context, False) # Changed Since 4126 PR
    if context_query:
        cmd = """
          SELECT * FROM (
            SELECT id, doc_id, pdq, url, context, bit_count_pdq(pdq # :pdq)
            AS score FROM images
          ) f
          WHERE score >= :threshold
          AND 
          """+context_query+"""
          ORDER BY score DESC
        """
    else:
        cmd = """
          SELECT * FROM (
            SELECT id, doc_id, pdq, url, context, bit_count_pdq(pdq # :pdq)
            AS score FROM images
          ) f
          WHERE score >= :threshold
          ORDER BY score DESC
        """
    if limit:
        cmd = cmd+" LIMIT :limit"
    matches = execute_command(text(cmd), dict(**{
      'pdq': pdq,
      'threshold': threshold,
      'limit': limit,
    }, **context_hash))
    keys = ('id', 'doc_id', 'pdq', 'url', 'context', 'score')
    rows = []
    for values in matches:
      row = dict(zip(keys, values))
      row["model"] = "image/pdq"
      rows.append(row)
    return rows
  except Exception as e:
    db.session.rollback()
    raise e