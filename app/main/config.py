import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
  SECRET_KEY = os.getenv('SECRET_KEY', 'my_precious_secret_key')
  DEBUG = False
  ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch:9200')
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
  MODEL_NAME = os.getenv('MODEL_NAME')
  MAX_CLAUSE_COUNT = 1000
  PERSISTENT_DISK_PATH = os.getenv('PERSISTENT_DISK_PATH', '/app/persistent_disk')
  VIDEO_MODEL = os.getenv('VIDEO_MODEL', 'video-model')
  try:
    VIDEO_MODEL_L1_SCORE = float(os.getenv('video_model_l1_score', '0.7'))
  except:
    VIDEO_MODEL_L1_SCORE = 0.7
  AUDIO_MODEL = os.getenv('AUDIO_MODEL', 'audio-model')
  

class DevelopmentConfig(Config):
  DEBUG = True

class TestingConfig(Config):
  DEBUG = True
  TESTING = True
  PRESERVE_CONTEXT_ON_EXCEPTION = False
  ELASTICSEARCH_SIMILARITY = 'alegre_similarity_test'
  REDIS_DATABASE = 0
  SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s/%(dbname)s?client_encoding=utf8' % {
    'user': os.getenv('DATABASE_USER', 'postgres'),
    'password': os.getenv('DATABASE_PASS', 'postgres'),
    'host': os.getenv('DATABASE_HOST', 'postgres'),
    'dbname': os.getenv('DATABASE_NAME', 'alegre_test'),
  }

class ProductionConfig(Config):
  DEBUG = False

config_by_name = dict(
  dev=DevelopmentConfig,
  test=TestingConfig,
  prod=ProductionConfig
)

key = Config.SECRET_KEY
