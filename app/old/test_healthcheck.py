import unittest
import json
from flask import current_app as app
from app.main import create_app
from unittest.mock import patch

from app.test.base import BaseTestCase

class TestHealthcheckBlueprint(BaseTestCase):
  def test_healthcheck_api_with_good_config(self):
    response = self.client.get('/healthcheck/')
    result = json.loads(response.data.decode())
    self.assertEqual('application/json', response.content_type)
    self.assertEqual(200, response.status_code)
    self.assertEqual(True, all(result['result']))

  def test_healthcheck_api_with_prod_env(self):
    with app.app_context():
      self.app = create_app(config_name="prod")
      response = self.client.get('/healthcheck/')
      result = json.loads(response.data.decode())
      self.assertEqual('application/json', response.content_type)
      self.assertEqual(200, response.status_code)
      self.assertEqual(True, all(result['result']))

class TestHealthcheckBlueprintWithBadConfig(BaseTestCase):

  def tearDown(self):
    # Don't call parent
    pass

  def test_healthcheck_api_with_non_existing_database(self):
    with app.app_context():
      app.config['SQLALCHEMY_DATABASE_URI']= 'postgresql+psycopg2://postgres:postgres@postgres/bad?client_encoding=utf8'
      response = self.client.get('/healthcheck/')
      self.assertEqual('application/json', response.content_type)
      self.assertEqual(500, response.status_code)

  def test_healthcheck_api_with_wrong_server(self):
    with app.app_context():
      app.config['SQLALCHEMY_DATABASE_URI']= 'postgresql+psycopg2://postgres:postgres@bad/bad?client_encoding=utf8'
      response = self.client.get('/healthcheck/')
      self.assertEqual('application/json', response.content_type)
      self.assertEqual(500, response.status_code)

  def test_healthcheck_api_elasticsearch_exception(self):
    with app.app_context():
      app.config['ELASTICSEARCH_URL']= ''
      response = self.client.get('/healthcheck/')
      self.assertEqual('application/json', response.content_type)
      self.assertEqual(500, response.status_code)

  def test_healthcheck_api_redis_error_connection(self):
    with app.app_context():
      app.config['REDIS_HOST']= ''
      response = self.client.get('/healthcheck/')
      self.assertEqual('application/json', response.content_type)
      self.assertEqual(500, response.status_code)

  def test_healthcheck_api_with_bad_config(self):
    with app.app_context():
      app.config['ELASTICSEARCH_URL']= 'bad'
      app.config['REDIS_HOST']= 'bad'
      app.config['SQLALCHEMY_DATABASE_URI']= 'bad'
      response = self.client.get('/healthcheck/')
      self.assertEqual('application/json', response.content_type)
      self.assertEqual(500, response.status_code)

  # def test_healthcheck_api_with_import_error(self):
  #   with patch.dict('sys.modules', {'app.main.lib.langid': None}):
  #     response = self.client.get('/healthcheck/')
  #     self.assertEqual('application/json', response.content_type)
  #     self.assertEqual(500, response.status_code)

if __name__ == '__main__':
    unittest.main()
