from flask import request, current_app as app
from flask_restplus import Resource, Namespace
from opensearchpy import OpenSearch
import os
import importlib
from sqlalchemy_utils import database_exists
from app.main import db
from app.main.lib import redis_client

api = Namespace('healthcheck', description='service healthcheck')

@api.route('/')
class HealthcheckResource(Resource):
  @api.response(200, 'healthcheck successfully queried.')
  @api.doc('Make a healthcheck query')
  def get(self):
    result = {
      'ELASTICSEARCH': False,
      'ELASTICSEARCH_SIMILARITY': False,
      'REDIS': False,
      'DATABASE': False,
      # 'LANGID': False
    }

    # Elasticsearch
    try:
      es = OpenSearch(app.config['ELASTICSEARCH_URL'], timeout=10, max_retries=3, retry_on_timeout=True)

    except Exception as e:
      result['ELASTICSEARCH'] = str(e)
    else:
      result['ELASTICSEARCH'] = True
      result['ELASTICSEARCH_SIMILARITY'] = True if es.indices.exists(
        index=[app.config['ELASTICSEARCH_SIMILARITY']]
      ) else 'Index not found `%s`' % app.config['ELASTICSEARCH_SIMILARITY']

    # Redis
    try:
      r = redis_client.get_client()
      result['REDIS'] = r.ping()
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

    # # Langid
    # try:
    #   class_ = getattr(importlib.import_module('app.main.lib.langid'), app.config['PROVIDER_LANGID'].title() + 'LangidProvider')
    #   result['LANGID'] = class_.test()
    # except Exception as e:
    #   result['LANGID'] = '%s: %s' % (app.config['PROVIDER_LANGID'].title() + 'LangidProvider', str(e))

    return { 'result': result }, 200 if all(x and type(x) == type(True) for x in result.values()) else 500
