from flask import current_app as app
from flask import request, current_app as app
from flask import current_app as app
from app.main import db
from app.main.model.image import ImageModel
from app.main.lib.helpers import context_matches
from app.main.lib.similarity_helpers import get_context_query, drop_context_from_record

from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound

app.app_context()
def _after_log(retry_state):
  app.logger.debug("Retrying image similarity...")

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
