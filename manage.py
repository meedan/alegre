import os
import unittest
import json

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from elasticsearch import Elasticsearch, TransportError
import sqlalchemy
from sqlalchemy.schema import DDL
from sqlalchemy_utils import database_exists, create_database
import json_logging

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
  if json_logging._current_framework is None:
    json_logging.init_flask(enable_json=True)
    json_logging.init_request_instrument(app)
  app.run(host='0.0.0.0', port=port, threaded=True)

@manager.command
def run_model():
  """Runs the model server."""
  if config_name == "test":
      model_config = json.load(open('./model_config_test.json')).get(app.config["MODEL_NAME"], {})
  else:
      model_config = json.load(open('./model_config.json')).get(app.config["MODEL_NAME"], {})
  SharedModel.start_server(
    model_config['class'],
    model_config['key'],
    model_config['options']
  )


@manager.command
def run_video_matcher():
  """Runs the video matcher."""
  VideoMatcher.start_server()

@manager.command
def init():
  """Initializes the service."""
  # Create ES indexes.
  es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
  try:
    if config_name == 'test':
      es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], ignore=[400, 404])
    es.indices.create(index=app.config['ELASTICSEARCH_SIMILARITY'])
  except TransportError as e:
    # ignore already existing index
    if e.error == 'resource_already_exists_exception':
      pass
    else:
      raise
  es.indices.put_mapping(
    body=json.load(open('./elasticsearch/alegre_similarity.json')),
    # include_type_name=True,
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
        CREATE OR REPLACE FUNCTION bit_count_image(value bigint)
        RETURNS integer
        AS $$ SELECT length(replace(value::bit(64)::text,'0','')); $$
        LANGUAGE SQL IMMUTABLE STRICT;
      """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION bit_count_audio(value bit(128))
        RETURNS integer
        AS $$ SELECT length(replace(value::text,'0','')); $$
        LANGUAGE SQL IMMUTABLE STRICT;
      """)
    )

    db.create_all()

    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION correlation(listx, listy)
        RETURNS float
        AS $$ 
            if len(listx) == 0 or len(listy) == 0:
                # Error checking in main program should prevent us from ever being
                # able to get here.
                raise Exception('Empty lists cannot be correlated.')
            if len(listx) > len(listy):
                listx = listx[:len(listy)]
            elif len(listx) < len(listy):
                listy = listy[:len(listx)]
            covariance = 0
            for i in range(len(listx)):
                covariance += 32 - bin(listx[i] ^ listy[i]).count("1")
            covariance = covariance / float(len(listx))
            return covariance/32
         $$ LANGUAGE plpythonu;
      """)
    )

    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION cross_correlation(listx, listy, offset, min_overlap)
        RETURNS float
        AS $$ 
            if offset > 0:
                listx = listx[offset:]
                listy = listy[:len(listx)]
            elif offset < 0:
                offset = -offset
                listy = listy[offset:]
                listx = listx[:len(listy)]
            if min(len(listx), len(listy)) < min_overlap:
                # Error checking in main program should prevent us from ever being
                # able to get here.
                return 
            #raise Exception('Overlap too small: %i' % min(len(listx), len(listy)))
            return correlation(listx, listy)
         $$ LANGUAGE plpythonu;
      """)
    )

    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION max_index(listx)
        RETURNS integer
        AS $$ 
            max_index = 0
            max_value = listx[0]
            for i, value in enumerate(listx):
                if value and max_value and value > max_value:
                    max_value = value
                    max_index = i
            return max_index
         $$ LANGUAGE plpythonu;
      """)
    )

    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION compare(listx, listy, span, step)
        RETURNS float[]
        AS $$ 
            if span > min(len(listx), len(listy)):
                span = min(len(listx), len(listy)) -1
            corr = []
            for offset in np.arange(-span, span + 1, step):
                corr.append(cross_correlation(listx, listy, offset))
            return corr
         $$ LANGUAGE plpythonu;
      """)
    )

    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION get_max_corr(corr, source, target, threshold, span, step)
        RETURNS integer
        AS $$ 
            max_corr_index = max_index(corr)
            max_corr_offset = -span + max_corr_index * step
            return corr[max_corr_index]
         $$ LANGUAGE plpythonu;
      """)
    )

    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION get_max_corr(corr, source, target, threshold, span, step)
        RETURNS integer
        AS $$ 
            max_corr_index = max_index(corr)
            max_corr_offset = -span + max_corr_index * step
            return corr[max_corr_index]
         $$ LANGUAGE plpythonu;
      """)
    )

    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION get_score(first, second, threshold, span, step)
        RETURNS float
        AS $$ 
            corr = compare(first, second, span, step)
            return get_max_corr(corr, first, second, threshold, span, step)
         $$ LANGUAGE plpythonu;
      """)
    )

@manager.command
def test(pattern='test*.py'):
  """Runs the unit tests."""
  tests = unittest.TestLoader().discover('app/test/', pattern=pattern)
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
