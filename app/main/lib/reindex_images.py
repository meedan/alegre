from flask import current_app as app
from flask import request, current_app as app
from flask import current_app as app
from app.main import db
from app.main.model.image import ImageModel
from app.main.lib.helpers import context_matches
from app.main.lib.similarity_helpers import get_context_query, drop_context_from_record
# from app.main.lib.image_similarity import add_image_pdq

from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound

def get_all_images(min_id,limit = 1000):
  try:
    cmd = """
      SELECT id, sha256, url, context,created_at,pdq  FROM images 
      WHERE pdq IS NULL AND id > :min_id 
      ORDER BY id 
      LIMIT :limit 
    """
    matches = db.session.execute(text(cmd), dict(**{
      'min_id': min_id,
      'limit': limit,
    })).fetchall()
    keys = ('id', 'sha256', 'url', 'context','created_at','pdq')
    rows = []
    for values in matches:
      row = dict(zip(keys, values))
      row["model"] = "image"
      rows.append(row)
    return rows
  except Exception as e:
    db.session.rollback()
    raise e

def calculate_pdq_for_all_images():
  from datetime import datetime

  rows = get_all_images(-1)
  while len(rows) > 0:
    print("starting a batch ")  # todo add time
    time_before = datetime.now()
    for item in rows:
      # print(item)
      add_image_pdq(item)
    time_after = datetime.now()


    delta = time_after - time_before
    print("ended a batch in:", delta.total_seconds())
    rows = get_all_images(rows[-1]['id'])

  return 1

# @tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
def alter_pdq(image):
  try:
    # First locate existing image and append new context
    existing = db.session.query(ImageModel).filter(ImageModel.id==image.id).one()
    existing.pdq = image.pdq
    flag_modified(existing, 'pdq')
    db.session.commit()
  except Exception as e:
    db.session.rollback()
    raise e

def add_image_pdq(save_params):
  try:
    image = ImageModel.from_url(save_params['url'], save_params.get('doc_id'), save_params['context'], save_params.get("created_at"))
    image.id = save_params['id']
    alter_pdq(image)
    return {
      'success': True
    }
  except Exception as e:
    print("error while processing image: ",save_params['url'])
    print(e)
    db.session.rollback()
    # raise e
