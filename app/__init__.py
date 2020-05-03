# app/__init__.py

from flask_restplus import Api
from flask import Blueprint

from .main.controller.about_controller import api as about_ns
from .main.controller.healthcheck_controller import api as healthcheck_ns
from .main.controller.langid_controller import api as langid_ns
from .main.controller.glossary_controller import api as glossary_ns
from .main.controller.similarity_controller import api as similarity_ns
from .main.controller.translation_controller import api as translation_ns
from .main.controller.model_controller import api as model_ns
from .main.controller.image_similarity_controller import api as image_similarity_ns
from .main.controller.image_classification_controller import api as image_classification_ns

blueprint = Blueprint('api', __name__)

api = Api(blueprint,
          title='Alegre API',
          version='2.0',
          description='A media analysis service'
          )

api.add_namespace(about_ns, path='/about')
api.add_namespace(healthcheck_ns, path='/healthcheck')
api.add_namespace(model_ns, path='/model')
api.add_namespace(langid_ns, path='/text/langid')
api.add_namespace(glossary_ns, path='/text/glossary')
api.add_namespace(similarity_ns, path='/text/similarity')
api.add_namespace(translation_ns, path='/text/translation')
api.add_namespace(image_similarity_ns, path='/image/similarity')
api.add_namespace(image_classification_ns, path='/image/classification')
