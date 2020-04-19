from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_restplus import Api
from flask_migrate import Migrate
from werkzeug.contrib.fixers import ProxyFix
import pybrake.flask
import logging
from .config import config_by_name

from gensim.models.keyedvectors import KeyedVectors
from .lib.docsim import DocSim
import os.path

db = SQLAlchemy()
flask_bcrypt = Bcrypt()
migrate = Migrate()

# Load language model.
# FIXME Load lazily when needed and move to appropriate controller.
ds = None
model_path = './data/model.txt'
if os.path.isfile(model_path):
  stopwords_path = './data/stopwords-en.txt'
  model = KeyedVectors.load_word2vec_format(model_path)
  with open(stopwords_path, 'r') as fh:
    stopwords = fh.read().split(',')
  ds = DocSim(model, stopwords=stopwords)

def create_app(config_name):
  app = Flask(__name__)
  app.config.from_object(config_by_name[config_name])
  app.wsgi_app = ProxyFix(app.wsgi_app)

  if config_name == 'prod':
    @property
    def specs_url(self):
      return url_for(self.endpoint('specs'), _external=True, _scheme='https')
    Api.specs_url = specs_url

  db.init_app(app)
  flask_bcrypt.init_app(app)
  migrate.init_app(app, db)

  with app.app_context():
    if os.getenv('AIRBRAKE_URL'):
      pybrake.flask.init_app(app)
      app.logger.addHandler(
        pybrake.LoggingHandler(notifier=app.extensions['pybrake'], level=logging.ERROR)
      )

  return app
