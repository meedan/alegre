import json
from flask import request, current_app as app
from flask import abort, jsonify
from flask_restplus import Resource, Namespace, fields
from app.main.lib.fields import JsonObject
from app.main.lib.shared_models.shared_model import SharedModel

api = Namespace('video_similarity', description='video similarity operations')
video_similarity_request = api.model('similarity_request', {
    'url': fields.String(required=True, description='text to be stored or queried for similarity'),
    'context': JsonObject(required=False, description='context'),
    'match_across_content_types': fields.Boolean(required=False, description='whether or not to search across content types when identifying matches (e.g. review audio channels from video sources, etc)'),
})
@api.route('/')
class VideoSimilarityResource(Resource):
    def model_response_package(self, request, command):
        context = request.json.get("context", {})
        context["content_type"] = "video"
        return {
            "url": request.json.get("url", {}),
            "doc_id": request.json.get("doc_id"),
            "context": context,
            "command": command,
            "threshold": request.json.get("threshold", 0.0),
            "match_across_content_types": request.json.get("match_across_content_types", False)
        }

    def request_video_task(self, request, command):
        model = SharedModel.get_client(app.config['VIDEO_MODEL'])
        app.logger.info("Request JSON for Video Similarity Request looks like "+str(json.dumps(request.json)))
        response = model.get_shared_model_response(self.model_response_package(request, command))
        return response

    # @api.response(200, 'video successfully deleted in the similarity database.')
    # @api.doc('Delete a video in the similarity database')
    # @api.expect(video_similarity_request, validate=True)
    # def delete(self):
    #     return self.request_video_task(request, "delete")

    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(video_similarity_request, validate=True)
    def post(self):
        return self.request_video_task(request, "add")

    @api.response(200, 'text similarity successfully queried.')
    @api.doc('Make a text similarity query')
    @api.expect(video_similarity_request, validate=True)
    def get(self):
        return self.request_video_task(request, "search")
