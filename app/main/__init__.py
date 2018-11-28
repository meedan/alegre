from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from elasticsearch import Elasticsearch, TransportError
from werkzeug.contrib.fixers import ProxyFix
import json

from .config import config_by_name

db = SQLAlchemy()
flask_bcrypt = Bcrypt()

def create_app(config_name):
  app = Flask(__name__)
  app.config.from_object(config_by_name[config_name])
  app.wsgi_app = ProxyFix(app.wsgi_app)
  db.init_app(app)
  flask_bcrypt.init_app(app)

  # Create ES index.
  es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
  for key in ['ELASTICSEARCH_GLOSSARY', 'ELASTICSEARCH_SIMILARITY']:
    try:
      es.indices.create(index=app.config[key])
    except TransportError as e:
      # ignore already existing index
      if e.error == 'resource_already_exists_exception':
        pass
      else:
        raise
  es.indices.put_mapping(
    doc_type='_doc',
    body=json.load(open('./elasticsearch/alegre_glossary.json')),
    index=app.config['ELASTICSEARCH_GLOSSARY']
  )
  es.indices.put_mapping(
    doc_type='_doc',
    body=json.load(open('./elasticsearch/alegre_similarity.json')),
    index=app.config['ELASTICSEARCH_SIMILARITY']
  )

  return app
