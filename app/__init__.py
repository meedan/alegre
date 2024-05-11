# app/__init__.py

from flask_restx import Api
from flask import Blueprint

from .main.controller.about_controller import api as about_ns
from .main.controller.healthcheck_controller import api as healthcheck_ns
from .main.controller.langid_controller import api as langid_ns
from .main.controller.similarity_controller import api as similarity_ns
from .main.controller.similarity_sync_controller import api as similarity_sync_ns
from .main.controller.similarity_async_controller import api as similarity_async_ns
from .main.controller.audio_transcription_controller import api as audio_transcription_ns
from .main.controller.audio_similarity_controller import api as audio_similarity_ns
from .main.controller.video_similarity_controller import api as video_similarity_ns
from .main.controller.bulk_similarity_controller import api as bulk_similarity_ns
from .main.controller.bulk_update_similarity_controller import api as bulk_update_similarity_ns
from .main.controller.translation_controller import api as translation_ns
from .main.controller.model_controller import api as model_ns
from .main.controller.image_similarity_controller import api as image_similarity_ns
from .main.controller.image_classification_controller import api as image_classification_ns
from .main.controller.image_ocr_controller import api as image_ocr_ns
from .main.controller.article_controller import api as article_ns
from .main.controller.graph_controller import api as graph_ns
from .main.controller.presto_controller import api as presto_ns

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
api.add_namespace(similarity_ns, path='/text/similarity')
api.add_namespace(similarity_async_ns, path='/similarity/async')
api.add_namespace(similarity_sync_ns, path='/similarity/sync')
api.add_namespace(audio_transcription_ns, path='/audio/transcription')
api.add_namespace(audio_similarity_ns, path='/audio/similarity')
api.add_namespace(video_similarity_ns, path='/video/similarity')
api.add_namespace(bulk_similarity_ns, path='/text/bulk_similarity')
api.add_namespace(bulk_update_similarity_ns, path='/text/bulk_update_similarity')
api.add_namespace(translation_ns, path='/text/translation')
api.add_namespace(image_similarity_ns, path='/image/similarity')
api.add_namespace(image_classification_ns, path='/image/classification')
api.add_namespace(image_ocr_ns, path='/image/ocr')
api.add_namespace(article_ns, path='/article')
api.add_namespace(graph_ns, path='/graph/cluster')
api.add_namespace(presto_ns, path='/presto')
