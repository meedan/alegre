from flask import request, current_app as app
from flask_restplus import Resource, Namespace
from elasticsearch import Elasticsearch
import redis
import os
import importlib
from app.main import db
from sqlalchemy_utils import database_exists

api = Namespace('healthcheck', description='service healthcheck')

@api.route('/')
class HealthcheckResource(Resource):
  @api.response(200, 'healthcheck successfully queried.')
  @api.doc('Make a healthcheck query')
  def get(self):
    result = {
      'ELASTICSEARCH': False,
      'ELASTICSEARCH_GLOSSARY': False,
      'ELASTICSEARCH_SIMILARITY': False,
      'REDIS': False,
      'DATABASE': False,
      'LANGID': False
    }

    # Elasticsearch
    try:
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=10, max_retries=3, retry_on_timeout=True)

    except Exception as e:
      result['ELASTICSEARCH'] = str(e)
    else:
      result['ELASTICSEARCH'] = True
      result['ELASTICSEARCH_GLOSSARY'] = True if es.indices.exists(
        index=[app.config['ELASTICSEARCH_GLOSSARY']]
      ) else 'Index not found `%s`' % app.config['ELASTICSEARCH_GLOSSARY']
      result['ELASTICSEARCH_SIMILARITY'] = True if es.indices.exists(
        index=[app.config['ELASTICSEARCH_SIMILARITY']]
      ) else 'Index not found `%s`' % app.config['ELASTICSEARCH_SIMILARITY']

    # Redis
    try:
      r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
      r.ping()
      result['REDIS'] = True
    except Exception as e:
      result['REDIS'] = str(e)

    # Postgres
    try:
      if (database_exists(app.config['SQLALCHEMY_DATABASE_URI'])):
        result['DATABASE'] = True
      else:
        result['DATABASE'] = 'Database not found `%s`' % app.config['SQLALCHEMY_DATABASE_URI']
    except Exception as e:
      result['DATABASE'] = str(e)

    # Langid
    try:
      class_ = getattr(importlib.import_module('app.main.lib.langid'), app.config['PROVIDER_LANGID'].title() + 'LangidProvider')
      result['LANGID'] = class_.test()
    except Exception as e:
      result['LANGID'] = '%s: %s' % (app.config['PROVIDER_LANGID'].title() + 'LangidProvider', str(e))

    return { 'result': result }, 200 if all(x and type(x) == type(True) for x in result.values()) else 500
