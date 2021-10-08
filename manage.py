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
def init_perl_functions():
  with app.app_context():
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE LANGUAGE plperl;
      """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION Correlation(integer[], integer[]) RETURNS float
        AS $$
            my @x=@{ $_[0]; };
            my @y=@{ $_[1]; };
            $len=scalar(@x);
            if (scalar(@x) > scalar(@y)) { 
               $len = scalar(@y);
            }
            $covariance = 0;
            for $i (0..$len-1) {
            $bits=0;
            $xor=@x[$i] ^ @y[$i];
            $bits=$xor;
            $bits = ($bits & 0x55555555) + (($bits & 0xAAAAAAAA) >> 1);
            $bits = ($bits & 0x33333333) + (($bits & 0xCCCCCCCC) >> 2);
            $bits = ($bits & 0x0F0F0F0F) + (($bits & 0xF0F0F0F0) >> 4);
            $bits = ($bits & 0x00FF00FF) + (($bits & 0xFF00FF00) >> 8);
            $bits = ($bits & 0x0000FFFF) + (($bits & 0xFFFF0000) >> 16);
            $covariance +=32 - $bits;
            }
            $covariance = $covariance / $len;
            return $covariance/32;
        $$
        LANGUAGE plperl;
      """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION CrossCorrelation(integer[], integer[], integer) RETURNS float
        AS $$
            my @x=@{ $_[0]; };
            my @y=@{ $_[1]; };
            my $offset=$_[2];
            my $min_overlap=20; #Change to 2 for debug.
            if ($offset > 0) {
                @x = @x[$offset..scalar(@x)-1]
            } if ($offset < 0) {
                $offset *= -1;
                @y = @y[$offset..scalar(@y)-1]
            }
            if (scalar(@x)<$min_overlap || scalar(@y) < $min_overlap) {
                # Error checking in main program should prevent us from ever being
                # able to get here.
                return 0;
             }
            return Correlation(\@x, \@y);
        $$
        LANGUAGE plperl;
      """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION CrossCorrelation(integer[], integer[], integer) RETURNS float
        AS $$
            my @x=@{ $_[0]; };
            my @y=@{ $_[1]; };
            my $offset=$_[2];
            my $min_overlap=20; #Change to 2 for debug.
            if ($offset > 0) {
                @x = @x[$offset..scalar(@x)-1]
            } if ($offset < 0) {
                $offset *= -1;
                @y = @y[$offset..scalar(@y)-1]
            }
            if (scalar(@x)<$min_overlap || scalar(@y) < $min_overlap) {
                # Error checking in main program should prevent us from ever being
                # able to get here.
                return 0;
             }
            return Correlation(\@x, \@y);
        $$
        LANGUAGE plperl;
      """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION Compare(integer[], integer[], integer) RETURNS float
        AS $$
            my @x=@{ $_[0]; };
            my @y=@{ $_[1]; };
            my $span=$_[2];
            my $step=1;
            if ($span > scalar(@x) || $span > scalar(@y)){
            	$span=scalar(@x)>scalar(@y)? scalar(@y) : scalar(@x);
            	$span--;
            }
            my @corr_xy;
            for $offset (-1*$span..$span){
            	push @corr_xy, CrossCorrelation(\@x, \@y, $offset);
            }
            return @corr_xy;
        $$
        LANGUAGE plperl;
      """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION MaxIndex(integer[]) RETURNS integer
        AS $$
            my @x=@{ $_[0]; };
            $maxi = 0;
            for $i (1..scalar(@x)-1) {
            	if (@x[$i]>@x[$maxi]) {
            		$maxi = $i;
            	}
            }
            return $maxi;
        $$
        LANGUAGE plperl;
      """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION GetScore(integer[], integer[]) RETURNS float
        AS $$
            my @first=@{ $_[0]; };
            my @second=@{ $_[1]; };
            my $span=150;
            my @corr = Compare(\@first, \@second, $span);
            my $max_corr_index = MaxIndex(\@corr);
            return @corr[$max_corr_index]
        $$
        LANGUAGE plperl;
      """)
    )
    db.create_all()

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
