# app/__init__.py

from flask_restplus import Api
from flask import Blueprint

from .main.controller.langid_controller import api as langid_ns
from .main.controller.spacy_controller import api as spacy_ns

blueprint = Blueprint('api', __name__)

api = Api(blueprint,
          title='Alegre API',
          version='2.0',
          description='A linguistic service for multilingual apps'
          )

api.add_namespace(langid_ns, path='/langid')
api.add_namespace(spacy_ns, path='/spacy')
