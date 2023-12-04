import json
from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from app.main.lib.fields import JsonObject

from app.main.lib import similarity

api = Namespace('video_similarity', description='video similarity operations')
video_similarity_request = api.model('similarity_request', {
    'url': fields.String(required=True, description='video URL to be stored or queried for similarity'),
    'context': JsonObject(required=False, description='context'),
    'match_across_content_types': fields.Boolean(required=False, description='whether or not to search across content types when identifying matches (e.g. review audio channels from video sources, etc)'),
})
@api.route('/')
class VideoSimilarityResource(Resource):
    @api.response(200, 'video successfully deleted in the similarity database.')
    @api.doc('Delete a video in the similarity database')
    @api.expect(video_similarity_request, validate=True)
    def delete(self):
        return similarity.delete_item(request.args, "video")

    @api.response(200, 'video successfully stored in the similarity database.')
    @api.doc('Store a video in the similarity database')
    @api.expect(video_similarity_request, validate=True)
    def post(self):
        return similarity.add_item(request.json, "video")

@api.route('/search/')
class VideoSimilaritySearchResource(Resource):
    @api.response(200, 'video similarity successfully queried.')
    @api.doc('Make a video similarity query. Note that we currently require GET requests with a JSON body rather than embedded params in the URL. You can achieve this via curl -X GET -H "Content-type: application/json" -H "Accept: application/json" -d \'{"url":"http://some.link/video.mp4", "threshold": 0.5}\' "http://[ALEGRE_HOST]/video/similarity"')
    @api.doc(params={'url': 'video URL to be stored or queried for similarity', 'threshold': 'minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)', 'context': 'context'} )
    def post(self):
        args = request.json
        app.logger.debug(f"Args are {args}")
        return similarity.get_similar_items(args, "video")
