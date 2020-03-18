import unittest
import json
from flask import current_app as app
from unittest.mock import patch

from app.test.base import BaseTestCase

class TestHealthcheckBlueprint(BaseTestCase):
  def test_healthcheck_api_with_good_config(self):
    response = self.client.get('/healthcheck/')
    result = json.loads(response.data.decode())
    self.assertEqual('application/json', response.content_type)
    self.assertEqual(200, response.status_code)
    self.assertEqual(True, all(result['result']))


class TestHealthcheckBlueprintWithBadConfig(BaseTestCase):
  def setUp(self):
    # Inject some bad config here
    # but don't call parent
    app.config.update({
      'ELASTICSEARCH_URL': 'bad',
      'REDIS_HOST': 'bad',
      'SQLALCHEMY_DATABASE_URI': 'bad'
    })

  def tearDown(self):
    # Don't call parent
    pass

  def test_healthcheck_api_with_bad_config(self):
    response = self.client.get('/healthcheck/')
    result = json.loads(response.data.decode())
    self.assertEqual('application/json', response.content_type)
    self.assertEqual(500, response.status_code)

if __name__ == '__main__':
    unittest.main()
