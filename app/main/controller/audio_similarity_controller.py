from flask import request, current_app as app
from flask import abort, jsonify
from flask_restplus import Resource, Namespace, fields
from elasticsearch import Elasticsearch
import elasticsearch
from app.main.lib.fields import JsonObject
from app.main.lib.shared_models.shared_model import SharedModel

api = Namespace('audio_similarity', description='audio similarity operations')
audio_similarity_request = api.model('similarity_request', {
    'url': fields.String(required=True, description='audio URL to be stored or queried for similarity'),
    'context': JsonObject(required=False, description='context'),
    'match_across_content_types': fields.Boolean(required=False, description='whether or not to search across content types when identifying matches (e.g. review audio channels from video sources, etc)'),
})
@api.route('/')
class AudioSimilarityResource(Resource):
    def model_response_package(self, request, command):
        if request.args.get('url'):
            url = request.args.get('url')
        elif request.json.get("url"):
            request.json.get("url", {})
        if(request.args.get('threshold')):
            threshold = request.args.get('threshold')
        elif(request.json.get("threshold")):
            threshold = request.json.get("threshold", {})
        if(request.args.get('context')):
            context = request.args.get('context')
        elif(request.json.get("context")):
            context = request.json.get("context", {})
        if(request.args.get('doc_id')):
            doc_id = request.args.get('doc_id')
        if not request.args.get('doc_id') and 'doc_id' in request.json:
            doc_id = request.json.get("doc_id", {})
        if(request.args.get('match_across_content_types')):
            match_across_content_types = request.args.get('match_across_content_types', False)
        if not request.args.get:
            match_across_content_types = request.json.get("match_across_content_types", False)

        context["content_type"] = "audio"
        return {
            "url": url,
            "doc_id": doc_id,
            "context": context,
            "command": command,
            "threshold": threshold,
            "match_across_content_types": match_across_content_types
        }

    def request_audio_task(self, request, command):
        model = SharedModel.get_client(app.config['AUDIO_MODEL'])
        response = model.get_shared_model_response(self.model_response_package(request, command))
        return response

    # @api.response(200, 'audio successfully deleted in the similarity database.')
    # @api.doc('Delete an audio in the similarity database')
    # @api.expect(audio_similarity_request, validate=True)
    # def delete(self):
    #     return self.request_audio_task(request, "delete")

    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(audio_similarity_request, validate=True)
    def post(self):
        return self.request_audio_task(request, "add")

    @api.response(200, 'text similarity successfully queried.')
    @api.doc('Make a text similarity query')
    @api.doc(params={'url': 'audio URL to be stored or queried for similarity', 'threshold': 'minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)', 'context': 'context'} )
    def get(self):
        return self.request_audio_task(request, "search")
