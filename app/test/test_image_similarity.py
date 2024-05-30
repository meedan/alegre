import unittest
import json
from flask import current_app as app
import numpy as np
from PIL import Image
from sqlalchemy import text
from unittest.mock import patch

from app.main import db
from app.test.base import BaseTestCase
from app.main.model.image import ImageModel
from app.main.lib.similarity_helpers import get_context_query

class TestImageSimilarityBlueprint(BaseTestCase):
  def test_bit_count(self):
    p = 45655524591978137 # the hash of the image above
    result = db.session.execute(text("SELECT BIT_COUNT_IMAGE(:p) AS test_count"), { 'p': p }).first()
    self.assertEqual(result['test_count'], 0.5625)

  def test_delete_image(self):
    url = 'file:///app/app/test/data/lenna-512.png'
    image = ImageModel(url=url, doc_id='1-2-3', context={'team_id': 1,'project_media_id': 1})
    db.session.add(image)
    db.session.commit()
    response = self.client.delete('/image/similarity/', data=json.dumps({
      'url': url,
      'doc_id': '1-2-3',
      'context': {
        'team_id': 1,
        'project_media_id': 1
      }
    }), content_type='application/json') # threshold should default to 0.9 == round(1 - 0.9) * 64.0 == 6
    result = json.loads(response.data.decode())
    self.assertEqual(True, result['deleted'])
    self.assertEqual(0, len(ImageModel.query.filter_by(url=url).all()))

if __name__ == '__main__':
  unittest.main()