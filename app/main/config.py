import os

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
  PROVIDER_LANGID = os.getenv('PROVIDER_LANGID', 'google')
  PROVIDER_IMAGE_CLASSIFICATION = os.getenv('PROVIDER_IMAGE_CLASSIFICATION', 'google')
  MS_TEXT_ANALYTICS_KEY = os.getenv('MS_TEXT_ANALYTICS_KEY')
  MS_TEXT_ANALYTICS_URL = os.getenv('MS_TEXT_ANALYTICS_URL', 'https://westcentralus.api.cognitive.microsoft.com/text/analytics/v2.1/')
  SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s/%(dbname)s?client_encoding=utf8' % {
    'user': os.getenv('DATABASE_USER', 'postgres'),
    'password': os.getenv('DATABASE_PASS', 'postgres'),
    'host': os.getenv('DATABASE_HOST', 'postgres'),
    'dbname': os.getenv('DATABASE_NAME', 'alegre'),
  }
  SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
  DEBUG = True
  FLASK_ENV = 'development'
  FLASK_DEBUG = True


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
    'dbname': 'alegre_test',
  }


class ProductionConfig(Config):
  DEBUG = False


config_by_name = dict(
  dev=DevelopmentConfig,
  test=TestingConfig,
  prod=ProductionConfig
)

key = Config.SECRET_KEY
