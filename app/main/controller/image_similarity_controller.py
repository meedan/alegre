from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from app.main import ds
from ..lib.fields import JsonObject

api = Namespace('image_similarity', description='image similarity operations')
image_similarity_request = api.model('image_similarity_request', {
    'url': fields.String(required=True, description='image URL to be stored or to query for similarity'),
    'threshold': fields.Float(required=False, description='minimum score to consider, between 0 and 1 (defaults to 0.7)'),
    'context': JsonObject(required=False, description='context')
})

@api.route('/')
class ImageSimilarityResource(Resource):
    @api.response(200, 'image signature successfully stored in the similarity database.')
    @api.doc('Store an image signature in the similarity database')
    @api.expect(imagesimilarity_request, validate=True)
    def post(self):
        result = False
        return {
            'success': success
        }


@api.route('/')
class ImageSimilarityQueryResource(Resource):
    @api.response(200, 'image similarity successfully queried.')
    @api.doc('Make an image similarity query')
    @api.expect(image_similarity_request, validate=True)
    def get(self):
        result = []
        return {
            'result': result
        }
