from flask import current_app as app
from flask import request, current_app as app
from flask import current_app as app
from app.main import db
from app.main.model.image import ImageModel
from app.main.lib.helpers import context_matches
from app.main.lib.similarity_helpers import get_context_query, drop_context_from_record
from app.main.lib.image_similarity import add_image_pdq

from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound

app.app_context()
def _after_log(retry_state):
  app.logger.debug("Retrying image similarity...")

def get_all_images():
  try:
    cmd = """
      SELECT id, sha256, url, context,created_at,pdq  FROM images
    """
    matches = db.session.execute(text(cmd)).fetchall()
    keys = ('id', 'sha256', 'url', 'context','created_at','pdq')
    rows = []
    for values in matches:
      row = dict(zip(keys, values))
      row["model"] = "image"
      row["context"] = ""

      rows.append(row)
    return rows
  except Exception as e:
    db.session.rollback()
    raise e

def calculate_pdq_for_all_images():
  rows = get_all_images()
  print(rows)
  for item in rows:
    add_image_pdq(item)

    return 1


# print("edy")
# print(calculate_pdq_for_all_images())
