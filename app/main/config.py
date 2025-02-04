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
  PROVIDER_LANGID = os.getenv('PROVIDER_LANGID', 'google')
  PROVIDER_IMAGE_CLASSIFICATION = os.getenv('PROVIDER_IMAGE_CLASSIFICATION', 'google')
  MS_TEXT_ANALYTICS_KEY = os.getenv('MS_TEXT_ANALYTICS_KEY')
  # MS_TEXT_ANALYTICS_URL = os.getenv('MS_TEXT_ANALYTICS_URL', 'https://westcentralus.api.cognitive.microsoft.com/text/analytics/v2.1/')
  SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s/%(dbname)s?client_encoding=utf8' % {
    'user': os.getenv('DATABASE_USER', 'postgres'),
    'password': os.getenv('DATABASE_PASS', 'postgres'),
    'host': os.getenv('DATABASE_HOST', 'postgres'),
    'dbname': os.getenv('DATABASE_NAME', 'alegre')
  }
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
  }
  MODEL_NAME = os.getenv('MODEL_NAME')
  MAX_CLAUSE_COUNT = 1000
  PERSISTENT_DISK_PATH = os.getenv('PERSISTENT_DISK_PATH', '/app/persistent_disk')
  try:
    VIDEO_MODEL_L1_SCORE = float(os.getenv('video_model_l1_score', '0.7'))
  except:
    VIDEO_MODEL_L1_SCORE = 0.7
  IMAGE_MODEL = os.getenv('IMAGE_MODEL', default='phash')
  OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', default=None)
  ALEGRE_HOST = os.getenv('ALEGRE_HOST', default="http://alegre:3100")
  PRESTO_HOST = os.getenv('PRESTO_HOST', default="http://presto:8000")
  CHECK_API_HOST = os.getenv('CHECK_API_HOST', default="http://api:3000")
  WEBHOOK_TOKEN = os.getenv('WEBHOOK_TOKEN', default="dev")
  S3_ENDPOINT = os.getenv("S3_ENDPOINT")
  AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
  AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
  AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

class DevelopmentConfig(Config):
  DEBUG = True

class TestingConfig(Config):
  DEBUG = True
  TESTING = True
  PRESERVE_CONTEXT_ON_EXCEPTION = False
  ELASTICSEARCH_SIMILARITY = 'alegre_similarity_test'
  REDIS_DATABASE =  os.getenv('REDIS_DATABASE', 1)
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
