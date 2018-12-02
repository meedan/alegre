# app/__init__.py

from flask_restplus import Api
from flask import Blueprint

from .main.controller.langid_controller import api as langid_ns
from .main.controller.spacy_controller import api as spacy_ns
from .main.controller.glossary_controller import api as glossary_ns
from .main.controller.similarity_controller import api as similarity_ns
from .main.controller.mt_controller import api as mt_ns
from .main.controller.wordvec_controller import api as wordvec_ns

blueprint = Blueprint('api', __name__)

api = Api(blueprint,
          title='Alegre API',
          version='2.0',
          description='A linguistic service for multilingual apps'
          )

api.add_namespace(langid_ns, path='/langid')
api.add_namespace(spacy_ns, path='/spacy')
api.add_namespace(glossary_ns, path='/glossary')
api.add_namespace(similarity_ns, path='/similarity')
api.add_namespace(mt_ns, path='/mt')
api.add_namespace(wordvec_ns, path='/wordvec')
