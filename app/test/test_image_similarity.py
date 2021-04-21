import unittest
import json
from flask import current_app as app
import numpy as np
from PIL import Image
from sqlalchemy import text
from unittest.mock import patch

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.image_hash import compute_phash_int
from app.main.model.image import ImageModel

class TestImageSimilarityBlueprint(BaseTestCase):
  def test_image_phash(self):
    im1 = Image.open('./app/test/data/lenna-512.jpg').convert('RGB')
    p1 = compute_phash_int(im1)
    im2 = Image.open('./app/test/data/lenna-512.png').convert('RGB')
    p2 = compute_phash_int(im2)
    self.assertEqual(p1, p2)

  def test_bit_count(self):
    p = 45655524591978137 # the hash of the image above
    result = db.session.execute(text("SELECT BIT_COUNT(:p) AS test_count"), { 'p': p }).first()
    self.assertEqual(result['test_count'], 28)

  def test_truncated_image_fetch(self):
    image = ImageModel.from_url('file:///app/app/test/data/truncated_img.jpg', '1-2-3')
    self.assertEqual(image.phash, 25444816931300591)

  def test_image_fetch(self):
    image = ImageModel.from_url('file:///app/app/test/data/lenna-512.png', '1-2-3')
    self.assertEqual(image.phash, 45655524591978137)

  def test_image_api(self):
    url = 'file:///app/app/test/data/lenna-512.png'

    # Test adding an image.
    response = self.client.post('/image/similarity/', data=json.dumps({
      'url': url,
      'context': {
        'team_id': 1,
        'project_media_id': 1
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(True, result['success'])
    self.assertEqual(1, len(ImageModel.query.filter_by(url=url).all()))

    # Test adding an identical image.
    response = self.client.post('/image/similarity/', data=json.dumps({
      'url': url,
      'context': {
        'team_id': 2,
        'project_media_id': 2
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(True, result['success'])
    image = ImageModel.from_url(url, '1-2-3')
    self.assertListEqual([
      {
        'team_id': 1,
        'project_media_id': 1
      },
      {
        'team_id': 2,
        'project_media_id': 2
      }
    ], ImageModel.query.filter_by(sha256=image.sha256).one().context)

    # Test searching by context.
    response = self.client.get('/image/similarity/', data=json.dumps({
      'context': {
        'project_media_id': 2
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(1, len(result['result']))

    # Test searching by context with array of possible values.
    response = self.client.get('/image/similarity/', data=json.dumps({
      'context': {
        'project_media_id': [2,3]
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(1, len(result['result']))

    # Test querying for identical images.
    url = 'file:///app/app/test/data/lenna-512.jpg'
    response = self.client.get('/image/similarity/', data=json.dumps({
      'url': url,
      'threshold': 1.0,
      'context': {}
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(1, len(result['result']))

    # Test querying with context.
    response = self.client.get('/image/similarity/', data=json.dumps({
      'url': url,
      'threshold': 1.0,
      'context': {
        'team_id': 1
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(1, len(result['result']))

    # Test querying for similar but not identical images.
    url = 'file:///app/app/test/data/lenna-256.png'
    response = self.client.get('/image/similarity/', data=json.dumps({
      'url': url,
      'threshold': 1.0,
      'context': {}
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(0, len(result['result']))
    response = self.client.get('/image/similarity/', data=json.dumps({
      'url': url,
      'context': {
        'team_id': 2
      }
    }), content_type='application/json') # threshold should default to 0.9 == round(1 - 0.9) * 64.0 == 6
    result = json.loads(response.data.decode())
    self.assertEqual(1, len(result['result']))

  def test_update_image(self):
    url = 'file:///app/app/test/data/lenna-512.png'
    # Test adding an image.
    response = self.client.post('/image/similarity/', data=json.dumps({
      'url': url,
      'doc_id': '1-2-3',
      'context': {
        'team_id': 1,
        'project_media_id': 1
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    url = 'file:///app/app/test/data/lenna-512.png'
    # Test adding an image.
    response = self.client.post('/image/similarity/', data=json.dumps({
      'url': url,
      'doc_id': '1-2-3',
      'context': {
        'team_id': 2,
        'project_media_id': 2
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    image = ImageModel.query.filter_by(url=url).all()[0]
    self.assertEqual(2, image.context[0]['team_id'])

  def test_delete_image(self):
    url = 'file:///app/app/test/data/lenna-512.png'
    # Test adding an image.
    response = self.client.post('/image/similarity/', data=json.dumps({
      'url': url,
      'doc_id': '1-2-3',
      'context': {
        'team_id': 1,
        'project_media_id': 1
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(True, result['success'])
    self.assertEqual(1, len(ImageModel.query.filter_by(url=url).all()))
    response = self.client.delete('/image/similarity/', data=json.dumps({
      'doc_id': '1-2-3'
    }), content_type='application/json') # threshold should default to 0.9 == round(1 - 0.9) * 64.0 == 6
    result = json.loads(response.data.decode())
    self.assertEqual(True, result['deleted'])
    self.assertEqual(0, len(ImageModel.query.filter_by(url=url).all()))


  def test_image_api_error(self):
    url = 'file:///app/app/test/data/lenna-512.png'

    with patch('sqlalchemy.orm.session.Session.commit') as mock_commit:
      mock_commit.side_effect = Exception('Simulated db.session.commit error')

      # Test adding an image.
      response = self.client.post('/image/similarity/', data=json.dumps({
        'url': url,
        'context': {
          'team_id': 1,
          'project_media_id': 1
        }
      }), content_type='application/json')
      result = json.loads(response.data.decode())
      self.assertEqual(500, response.status_code)

    with patch('sqlalchemy.orm.session.Session.execute') as mock_execute:
      mock_execute.side_effect = Exception('Simulated db.session.execute error')

      # Test adding an image.
      response = self.client.get('/image/similarity/', data=json.dumps({
        'url': url,
        'context': {
          'team_id': 1,
          'project_media_id': 1
        }
      }), content_type='application/json')
      result = json.loads(response.data.decode())
      self.assertEqual(500, response.status_code)

if __name__ == '__main__':
  unittest.main()
