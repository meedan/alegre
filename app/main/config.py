import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
  SECRET_KEY = os.getenv('SECRET_KEY', 'my_precious_secret_key')
  DEBUG = False
  ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch:9200')
  ELASTICSEARCH_GLOSSARY = 'alegre_glossary'
  ELASTICSEARCH_SIMILARITY = 'alegre_similarity'
  REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
  REDIS_PORT = os.getenv('REDIS_PORT', 6379)
  REDIS_DATABASE = os.getenv('REDIS_DATABASE', 0)
  PYBRAKE = {
    'project_id': 1,
    'project_key': os.getenv('AIRBRAKE_PROJECT_KEY'),
    'host': os.getenv('AIRBRAKE_URL'),
    'environment': os.getenv('AIRBRAKE_ENVIRONMENT', os.getenv('BOILERPLATE_ENV')),
    'apm_disabled': True
  }
  PROVIDER_LANGID = os.getenv('PROVIDER_LANGID', 'google')
  PROVIDER_IMAGE_CLASSIFICATION = os.getenv('PROVIDER_IMAGE_CLASSIFICATION', 'google')
  MS_TEXT_ANALYTICS_KEY = os.getenv('MS_TEXT_ANALYTICS_KEY')
  MS_TEXT_ANALYTICS_URL = os.getenv('MS_TEXT_ANALYTICS_URL', 'https://westcentralus.api.cognitive.microsoft.com/text/analytics/v2.1/')
  SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s/%(dbname)s?client_encoding=utf8' % {
    'user': os.getenv('DATABASE_USER', 'postgres'),
    'password': os.getenv('DATABASE_PASS', 'postgres'),
    'host': os.getenv('DATABASE_HOST', 'postgres'),
    'dbname': os.getenv('DATABASE_NAME', 'alegre')
  }
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True
  }
  MODEL_CLASS = os.getenv('MODEL_CLASS')
  MODEL_KEY = os.getenv('MODEL_KEY')
  MODEL_OPTIONS = json.loads(os.getenv('MODEL_OPTIONS', '{}'))

class DevelopmentConfig(Config):
  DEBUG = True

class TestingConfig(Config):
  DEBUG = True
  TESTING = True
  PRESERVE_CONTEXT_ON_EXCEPTION = False
  ELASTICSEARCH_GLOSSARY = 'alegre_glossary_test'
  ELASTICSEARCH_SIMILARITY = 'alegre_similarity_test'
  REDIS_DATABASE = 1
  SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s/%(dbname)s?client_encoding=utf8' % {
    'user': os.getenv('DATABASE_USER', 'postgres'),
    'password': os.getenv('DATABASE_PASS', 'postgres'),
    'host': os.getenv('DATABASE_HOST', 'postgres'),
    'dbname': 'alegre_test'
  }

class ProductionConfig(Config):
  DEBUG = False

config_by_name = dict(
  dev=DevelopmentConfig,
  test=TestingConfig,
  prod=ProductionConfig
)

key = Config.SECRET_KEY
