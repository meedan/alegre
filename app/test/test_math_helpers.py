import unittest
import json
import uuid
from flask import current_app as app
import redis

from app.test.base import BaseTestCase
from app.main.lib.shared_models.wordvec import WordVec
from app.main.lib.math_helpers import (
  similarity_for_model_name,
  similarity_for_model,
  cosine_sim,
  angular_similarity,
)
class TestMathHelpers(BaseTestCase):
  def setUp(self):
    r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
    r.flushall()

  def test_similarity_for_model_name(self):
    self.assertEqual(similarity_for_model_name("WordVec", [1,2,3], [1,2,3]), 1)

  def test_similarity_for_model(self):
    self.assertEqual(similarity_for_model(WordVec(), [1,2,3], [1,2,3]), 1)

  def test_cosine_sim(self):
    self.assertEqual(cosine_sim([1,2,3], [1,2,3]), 1)

  def test_angular_similarity(self):
    self.assertEqual(angular_similarity([1,2,3], [1,2,3]), 1)

if __name__ == '__main__':
    unittest.main()
