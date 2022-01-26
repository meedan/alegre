from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from app.main.lib.fields import JsonObject

from app.main.lib import similarity

api = Namespace('audio_similarity', description='audio similarity operations')
audio_similarity_request = api.model('similarity_request', {
    'url': fields.String(required=True, description='audio URL to be stored or queried for similarity'),
    'context': JsonObject(required=False, description='context'),
    'match_across_content_types': fields.Boolean(required=False, description='whether or not to search across content types when identifying matches (e.g. review audio channels from video sources, etc)'),
})
@api.route('/')
class AudioSimilarityResource(Resource):
    @api.response(200, 'audio successfully deleted in the similarity database.')
    @api.doc('Delete an audio in the similarity database')
    @api.expect(audio_similarity_request, validate=True)
    def delete(self):
        return similarity.delete_item(request.args or request.json, "audio")

    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(audio_similarity_request, validate=True)
    def post(self):
        return similarity.add_item(request.args or request.json, "audio")

    @api.response(200, 'text similarity successfully queried.')
    @api.doc('Make a text similarity query')
    @api.doc(params={'url': 'audio URL to be stored or queried for similarity', 'threshold': 'minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)', 'context': 'context'} )
    def get(self):
        return similarity.get_similar_items(request.args or request.json, "audio")
