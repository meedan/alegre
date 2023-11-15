import urllib.parse
import unittest
import json
from flask import current_app as app
import numpy as np
from PIL import Image
from sqlalchemy import text
from unittest.mock import patch

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.image_hash import compute_phash_int, phash2int, compute_dhash, compute_ahash, compute_whash
from app.main.model.image import ImageModel
from app.main.lib.similarity_helpers import get_context_query

class TestImageSimilarityBlueprint(BaseTestCase):
  def test_image_phash(self):
    im1 = Image.open('./app/test/data/lenna-512.jpg').convert('RGB')
    p1 = compute_phash_int(im1)
    im2 = Image.open('./app/test/data/lenna-512.png').convert('RGB')
    p2 = compute_phash_int(im2)
    self.assertEqual(p1, p2)

    im3 = Image.open('./app/test/data/lenna-256.png').convert('RGB')
    p3 = phash2int(compute_dhash(im3))
    p2 = phash2int(compute_dhash(im2))
    self.assertNotEqual(p2, p3)

    p4 = phash2int(compute_ahash(im1))
    p5 = phash2int(compute_ahash(im2))
    self.assertEqual(p4, p5)

    p6 = phash2int(compute_whash(im1))
    p7 = phash2int(compute_whash(im2))
    self.assertEqual(p6, p7)

  def test_image_phash_error(self):
    with patch('PIL.Image.Image.verify') as mock:
      mock.side_effect = Exception('PIL.UnidentifiedImageError')
      with self.assertRaises(Exception):
        im1 = Image.open('./app/test/data/lenna-512.jpg').convert('RGB')
        p1 = compute_phash_int(im1)

  def test_bit_count(self):
    p = 45655524591978137 # the hash of the image above
    result = db.session.execute(text("SELECT BIT_COUNT_IMAGE(:p) AS test_count"), { 'p': p }).first()
    self.assertEqual(result['test_count'], 0.5625)

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
    lookup = urllib.parse.urlencode({'context': json.dumps({'team_id': 2})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(1, len(result['result']))

    # Test searching by context with array of possible values.
    lookup = urllib.parse.urlencode({'context': json.dumps({'team_id': [2, 3]})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(1, len(result['result']))

    # Test searching by context with array of possible values, where no response should be found.
    lookup = urllib.parse.urlencode({'context': json.dumps({'team_id': [-1, -2]})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(0, len(result['result']))

    # Test querying for identical images.
    url = 'file:///app/app/test/data/lenna-512.jpg'
    lookup = urllib.parse.urlencode({'url': url, 'threshold': 1.0, 'context': json.dumps({})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(1, len(result['result']))

    # Test querying with context.
    lookup = urllib.parse.urlencode({'url': url, 'threshold': 1.0, 'context': json.dumps({'team_id': 1})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(1, len(result['result']))

    # Test querying with multi context.
    lookup = urllib.parse.urlencode({'url': url, 'threshold': 1.0, 'context': json.dumps({'team_id': [1, 2, 3]})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(1, len(result['result']))

    # Test empty querying with multi context.
    lookup = urllib.parse.urlencode({'url': url, 'threshold': 1.0, 'context': json.dumps({'team_id': [-1, -2]})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(0, len(result['result']))

    # Test querying for similar but not identical images.
    url = 'file:///app/app/test/data/lenna-256.png'
    lookup = urllib.parse.urlencode({'url': url, 'threshold': 1.0, 'context': json.dumps({})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(0, len(result['result']))
    lookup = urllib.parse.urlencode({'url': url, 'context': json.dumps({'team_id': 2})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
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
      lookup = urllib.parse.urlencode({'url': url, 'context': json.dumps({'team_id': 1, 'project_media_id': 1})})
      response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
      self.assertEqual(500, response.status_code)

  def test_add_image_error(self):
    url = 'file:///app/app/test/data/lenna-512.png'

    with patch('sqlalchemy.orm.attributes.flag_modified'):
      with patch('sqlalchemy.orm.exc.NoResultFound') as mock:
        mock.side_effect = Exception('')
        response = self.client.post('/image/similarity/', data=json.dumps({
          'url': url,
          'context': {
            'team_id': 1,
            'project_media_id': 1
          }
        }), content_type='application/json')
        self.assertEqual(500, response.status_code)

  def test_search_by_context_error(self):
    url = 'file:///app/app/test/data/lenna-512.png'
    response = self.client.post('/image/similarity/', data=json.dumps({
      'url': url,
      'context': {
        'team_id': 2,
        'project_media_id': 1
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(True, result['success'])
    lookup = urllib.parse.urlencode({'context': json.dumps({'team_id': 'aa'})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    self.assertEqual(500, response.status_code)
    result = json.loads(response.data.decode())

  def test_search_with_empty_context(self):
    url = 'file:///app/app/test/data/lenna-512.png'
    response = self.client.post('/image/similarity/', data=json.dumps({
      'url': url,
      'context': {
        'team_id': 2,
        'project_media_id': 1
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(True, result['success'])
    lookup = urllib.parse.urlencode({'context': json.dumps({})})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    self.assertEqual(200, response.status_code)

  def test_search_using_url(self):
    url = 'file:///app/app/test/data/lenna-512.png'
    context = { 'team_id': 2}
    response = self.client.post('/image/similarity/', data=json.dumps({
      'url': url,
      'context': {
        'team_id': 2,
        'project_media_id': 1
      }
    }), content_type='application/json')
    result = json.loads(response.data.decode())
    self.assertEqual(True, result['success'])
    lookup = urllib.parse.urlencode({'url': url})
    response = self.client.get('/image/similarity/?'+lookup, content_type='application/json')
    result = get_context_query(context, False, True)
    self.assertIn({'context_team_id': 2}, result)

if __name__ == '__main__':
  unittest.main()
