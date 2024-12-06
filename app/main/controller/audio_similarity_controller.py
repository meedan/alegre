import json
from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from app.main.lib.fields import JsonObject

from app.main.lib import similarity
from flask import jsonify

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
        return similarity.delete_item(request.json or request.args, "audio") # Changed Since 4126 PR

    @api.response(200, 'audio successfully stored in the similarity database.')
    @api.doc('Store an audio in the similarity database')
    @api.expect(audio_similarity_request, validate=True)
    def post(self):
        return jsonify({"message": "This endpoint is not implemented."}), 501

@api.route('/search/')
class AudioSimilaritySearchResource(Resource):
    @api.response(200, 'text similarity successfully queried.')
    @api.doc('Make an audio similarity query. Note that we currently require GET requests with a JSON body rather than embedded params in the URL. You can achieve this via curl -X GET -H "Content-type: application/json" -H "Accept: application/json" -d \'{"url":"http://some.link/video.mp3", "threshold": 0.5}\' "http://[ALEGRE_HOST]/audio/similarity"')
    @api.doc(params={'url': 'audio URL to be stored or queried for similarity', 'threshold': 'minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)', 'context': 'context'} )
    def post(self):
        args = request.json
        return jsonify({"message": "This endpoint is not implemented."}), 501
