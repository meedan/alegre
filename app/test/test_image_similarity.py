import unittest
import json
from flask import current_app as app
import numpy as np
from PIL import Image
from sqlalchemy import text

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.imagehash import compute_phash_int
from app.main.model.image import ImageModel

class TestImageSimilaryBlueprint(BaseTestCase):
  def test_image_phash(self):
    im1 = Image.open('./app/test/data/lenna-512.jpg').convert('RGB')
    p1 = compute_phash_int(im1)
    im2 = Image.open('./app/test/data/lenna-512.png').convert('RGB')
    p2 = compute_phash_int(im2)
    im3 = Image.open('./app/test/data/lenna-256.png').convert('RGB')
    p3 = compute_phash_int(im3)
    self.assertEqual(p1, p2)
    self.assertEqual(p1, p3)

  def test_bit_count(self):
    p = 45655524591978137 # the hash of the image above
    result = db.session.execute(text("SELECT BIT_COUNT(:p) AS test_count"), { 'p': p }).first()
    self.assertEqual(result['test_count'], 28)

  def test_image_fetch(self):
    image = ImageModel.from_url('file:///app/app/test/data/lenna-512.png')
    self.assertEqual(image.phash, 45655524591978137)

  def test_image_api(self):
    url = 'file:///app/app/test/data/lenna-512.png'
    with self.client:
      response = self.client.post('/image/similarity/', data=json.dumps({
        'url': url,
        'threshold': 0,
        'context': {}
      }), content_type='application/json')
      result = json.loads(response.data.decode())
      self.assertEqual(True, result['success'])
      self.assertEqual(1, len(ImageModel.query.filter_by(url=url).all()))

      url = 'file:///app/app/test/data/lenna-512.jpg'
      response = self.client.get('/image/similarity/', data=json.dumps({
        'url': url,
        'threshold': 0,
        'context': {}
      }), content_type='application/json')
      result = json.loads(response.data.decode())
      self.assertEqual(1, len(result['result']))


if __name__ == '__main__':
  unittest.main()
