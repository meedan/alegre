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

if __name__ == '__main__':
    unittest.main()
