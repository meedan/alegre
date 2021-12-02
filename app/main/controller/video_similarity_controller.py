from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from app.main.lib.fields import JsonObject

from app.main.lib import similarity

api = Namespace('video_similarity', description='video similarity operations')
video_similarity_request = api.model('similarity_request', {
    'url': fields.String(required=True, description='text to be stored or queried for similarity'),
    'context': JsonObject(required=False, description='context'),
    'match_across_content_types': fields.Boolean(required=False, description='whether or not to search across content types when identifying matches (e.g. review audio channels from video sources, etc)'),
})
@api.route('/')
class VideoSimilarityResource(Resource):
    @api.response(200, 'video successfully deleted in the similarity database.')
    @api.doc('Delete a video in the similarity database')
    @api.expect(video_similarity_request, validate=True)
    def delete(self):
        return similarity.delete_item(request.json, "video")

    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(video_similarity_request, validate=True)
    def post(self):
        return similarity.add_item(request.json, "video")

    @api.response(200, 'text similarity successfully queried.')
    @api.doc('Make a text similarity query')
    @api.expect(video_similarity_request, validate=True)
    def get(self):
        return similarity.get_similar_items(request.json, "video")
