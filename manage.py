import os
import unittest
import json

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from elasticsearch import Elasticsearch, TransportError
import sqlalchemy
from sqlalchemy.schema import DDL
from sqlalchemy_utils import database_exists, create_database

from app import blueprint
from app.main import create_app, db
from app.main.model import image
from app.main.lib.shared_models.shared_model import SharedModel

from app.main.lib.image_hash import compute_phash_int
from PIL import Image

# Don't remove this line until https://github.com/tensorflow/tensorflow/issues/34607 is fixed
# (by upgrading to tensorflow 2.2 or higher)
import tensorflow as tf

config_name = os.getenv('BOILERPLATE_ENV', 'dev')
app = create_app(config_name)
app.register_blueprint(blueprint)
app.app_context().push()

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

@manager.command
def run():
  """Runs the API server."""
  port = os.getenv('ALEGRE_PORT', 5000)
  app.run(host='0.0.0.0', port=port, threaded=True)

@manager.command
def run_model():
  """Runs the model server."""
  SharedModel.start_server(
    app.config['MODEL_CLASS'],
    app.config['MODEL_KEY'],
    app.config['MODEL_OPTIONS']
  )

@manager.command
def init():
  """Initializes the service."""
  # Create ES index.
  es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
  for key in ['ELASTICSEARCH_GLOSSARY', 'ELASTICSEARCH_SIMILARITY']:
    try:
      if config_name == 'test':
        es.indices.delete(index=app.config[key], ignore=[400, 404])
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
  es.indices.close(index=app.config['ELASTICSEARCH_SIMILARITY'])
  es.indices.put_settings(
    body=json.load(open('./elasticsearch/alegre_similarity_settings.json')),
    index=app.config['ELASTICSEARCH_SIMILARITY']
  )
  es.indices.open(index=app.config['ELASTICSEARCH_SIMILARITY'])
  es.indices.put_mapping(
    doc_type='_doc',
    body=json.load(open('./elasticsearch/alegre_similarity.json')),
    index=app.config['ELASTICSEARCH_SIMILARITY']
  )

  # Create database.
  with app.app_context():
    if not database_exists(db.engine.url):
      create_database(db.engine.url)

    if config_name == 'test':
      db.drop_all()

    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION bit_count(value bigint)
        RETURNS integer
        AS $$ SELECT length(replace(value::bit(64)::text,'0','')); $$
        LANGUAGE SQL IMMUTABLE STRICT;
      """)
    )

    db.create_all()

@manager.command
def test(pattern='test*.py'):
  """Runs the unit tests."""
  tests = unittest.TestLoader().discover('app/test', pattern=pattern)
  result = unittest.TextTestRunner(verbosity=2).run(tests)
  return 0 if result.wasSuccessful() else 1

@manager.command
def phash(path):
  """Computes the phash of a given image."""
  im = Image.open(path).convert('RGB')
  phash = compute_phash_int(im)
  print(phash, "{0:b}".format(phash), sep=" ")

if __name__ == '__main__':
  manager.run()
