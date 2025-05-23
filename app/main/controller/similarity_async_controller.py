import json
from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields

from app.main.lib.fields import JsonObject
from app.main.lib import similarity
from app.main.lib.webhook import Webhook

api = Namespace('similarity_async', description='asynchronous similarity operations')
similarity_async_request = api.model('similarity_async_request', {
    'text': fields.String(required=False, description='text to be stored or queried for similarity'),
    'url': fields.String(required=False, description='url for item to be stored or queried for similarity'),
    'callback_url': fields.String(required=False, description='callback_url for final search results'),
    'content_hash': fields.String(required=False, description='Content hash for checking for cached Presto Response'),
    'doc_id': fields.String(required=False, description='text ID to constrain uniqueness'),
    'models': fields.List(required=False, description='similarity models to use: ["elasticsearch"] (pure Elasticsearch, default) or the key name of an active model', cls_or_instance=fields.String),
    'language': fields.String(required=False, description='language code for the analyzer to use during the similarity query (defaults to standard analyzer)'),
    'threshold': fields.Float(required=False, description='minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)'),
    'context': JsonObject(required=True, description='context'),
    'fuzzy': fields.Boolean(required=False, description='whether or not to use fuzzy search on GET queries (only used when model is set to \'elasticsearch\')'),
    'requires_callback': fields.Boolean(required=False, description='whether or not to trigger a callback event to the provided URL'),
})
@api.route('/<string:similarity_type>')
class AsyncSimilarityResource(Resource):
    @api.response(200, 'text similarity successfully queried.')
    @api.doc('Make a text similarity query. Note that we currently require GET requests with a JSON body rather than embedded params in the URL. You can achieve this via curl -X GET -H "Content-type: application/json" -H "Accept: application/json" -d \'{"text":"Some Text", "threshold": 0.5, "model": "elasticsearch"}\' "http://[ALEGRE_HOST]/text/similarity"')
    @api.doc(params={'text': 'text to be stored or queried for similarity', 'threshold': 'minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)', 'model': 'similarity model to use: "elasticsearch" (pure Elasticsearch, default) or the key name of an active model'})
    def post(self, similarity_type):
        args = request.json
        app.logger.info(f"[AsyncSimilarityResource] Starting Request - args are {args}, similarity_type is {similarity_type}")
        if similarity_type == "text":
            package = similarity.get_body_for_text_document(args, 'query')
        else:
            package = similarity.get_body_for_media_document(args, 'query')
        # Default to true for this endpoint instead of false in most other cases
        package["suppress_response"] = args.get("suppress_response", False)
        package["requires_callback"] = args.get("requires_callback", True)
        response, waiting_for_callback = similarity.async_get_similar_items(package, similarity_type)
        if not waiting_for_callback:
            package.pop("created_at", None)
            result = similarity.callback_search_item({"raw": package}, similarity_type)
            result["is_shortcircuited_search_result_callback"] = True
            callback_url = args.get("callback_url", app.config['CHECK_API_HOST']) or app.config['CHECK_API_HOST']
            Webhook.return_webhook(callback_url, "search", similarity_type, result)
        app.logger.info(f"[AsyncSimilarityResource] Completing Request - args are {args}, similarity_type is {similarity_type}, reponse is {response}")
        return response
