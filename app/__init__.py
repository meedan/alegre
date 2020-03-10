# app/__init__.py

from flask_restplus import Api
from flask import Blueprint

from .main.controller.langid_controller import api as langid_ns
from .main.controller.glossary_controller import api as glossary_ns
from .main.controller.similarity_controller import api as similarity_ns
from .main.controller.translation_controller import api as translation_ns
from .main.controller.wordvec_controller import api as wordvec_ns
from .main.controller.image_similarity_controller import api as image_similarity_ns

blueprint = Blueprint('api', __name__)

api = Api(blueprint,
          title='Alegre API',
          version='2.0',
          description='A linguistic service for multilingual apps'
          )

api.add_namespace(langid_ns, path='/text/langid')
api.add_namespace(glossary_ns, path='/text/glossary')
api.add_namespace(similarity_ns, path='/text/similarity')
api.add_namespace(translation_ns, path='/text/translation')
api.add_namespace(wordvec_ns, path='/text/wordvec')
api.add_namespace(image_similarity_ns, path='/image/similarity')
