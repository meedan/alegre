from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_restplus import Api
from werkzeug.contrib.fixers import ProxyFix
import pybrake.flask
import logging
from .config import config_by_name
from app.main.lib.docsim import DocSim
from app.main.lib.universal_sentence_encoder import UniversalSentenceEncoder

db = SQLAlchemy()
flask_bcrypt = Bcrypt()
language_models = {e.model_name(): e for e in [DocSim.start_client(), UniversalSentenceEncoder.start_client()]}
DEFAULT_LANGUAGE_MODEL = "UniversalSentenceEncoder"
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

  with app.app_context():
    if app.config['PYBRAKE']['project_key']:
      pybrake.flask.init_app(app)
      app.logger.addHandler(
        pybrake.LoggingHandler(notifier=app.extensions['pybrake'], level=logging.ERROR)
      )

  return app
