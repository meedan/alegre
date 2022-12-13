from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_restx import Api
from flask_migrate import Migrate
from werkzeug.contrib.fixers import ProxyFix
import pybrake.flask
import logging
from .config import config_by_name

db = SQLAlchemy()
flask_bcrypt = Bcrypt()
migrate = Migrate()

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
    # Init JSON logging, only once to avoid exceptions during tests
    if app.config['PYBRAKE']['project_key']:
      pybrake.flask.init_app(app)
      app.logger.addHandler(
        pybrake.LoggingHandler(notifier=app.extensions['pybrake'], level=logging.ERROR)
      )
    logging.basicConfig(level=logging.INFO)

  return app
