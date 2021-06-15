from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
import json
import numpy as np
import sys
import inspect
from app.main.lib.shared_models.shared_model import SharedModel
import app.main.lib.langid
import app.main.lib.image_classification

api = Namespace('about', description='service information')

@api.route('/')
class AboutResource(Resource):
    @api.response(200, 'successfully retrieved information about service.')
    @api.doc('Retrieve information about Alegre')
    def get(self):
        return {
            'text/langid': AboutResource.list_providers('app.main.lib.langid', 'LangidProvider'),
            'text/translation': ['google'],
            'text/similarity': ['elasticsearch'] + SharedModel.get_servers(),
            'text/bulk_similarity': ['elasticsearch'],
            'text/bulk_upload_similarity': SharedModel.get_servers(),
            'image/classification': AboutResource.list_providers('app.main.lib.image_classification', 'ImageClassificationProvider'),
            'image/similarity': ['phash'],
            'image/ocr': ['google']
        }

    @staticmethod
    def list_providers(module, suffix):
        # https://stackoverflow.com/a/1796247/209184
        return [c[0].replace(suffix, '').lower() for c in inspect.getmembers(sys.modules[module], inspect.isclass)]
