from flask import request, current_app as app
from flask import abort, jsonify
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
import elasticsearch
from app.main.lib.fields import JsonObject
from app.main.lib.shared_models.shared_model import SharedModel

api = Namespace('video_similarity', description='video similarity operations')
video_similarity_request = api.model('similarity_request', {
    'url': fields.String(required=True, description='text to be stored or queried for similarity'),
    'context': JsonObject(required=False, description='context'),
})
@api.route('/')
class VideoSimilarityResource(Resource):
    def model_response_package(self, request, command):
        return {
            "url": request.json.get("url", {}),
            "doc_id": request.json.get("doc_id"),
            "context": request.json.get("context", {}),
            "command": command
        }

    def request_video_task(self, request, command):
        model = SharedModel.get_client(app.config['VIDEO_MODEL'])
        response = model.get_shared_model_response(self.model_response_package(request, command))
        return response

    # @api.response(200, 'text successfully deleted in the similarity database.')
    # @api.doc('Delete a text in the similarity database')
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
