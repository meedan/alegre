import json
from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields

from app.main.lib.fields import JsonObject
from app.main.lib import similarity

api = Namespace('similarity_sync', description='synchronous similarity operations')
similarity_sync_request = api.model('similarity_sync_request', {
    'text': fields.String(required=False, description='text to be stored or queried for similarity'),
    'url': fields.String(required=False, description='url for item to be stored or queried for similarity'),
    'doc_id': fields.String(required=False, description='text ID to constrain uniqueness'),
    'models': fields.List(required=False, description='similarity models to use: ["opensearch"] (pure OpenSearch, default) or the key name of an active model', cls_or_instance=fields.String),
    'language': fields.String(required=False, description='language code for the analyzer to use during the similarity query (defaults to standard analyzer)'),
    'threshold': fields.Float(required=False, description='minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)'),
    'context': JsonObject(required=True, description='context'),
    'fuzzy': fields.Boolean(required=False, description='whether or not to use fuzzy search on GET queries (only used when model is set to \'opensearch\')'),
})
@api.route('/<string:similarity_type>')
class SyncSimilarityResource(Resource):
    @api.response(200, 'text similarity successfully queried.')
    @api.doc('Make a text similarity query. Note that we currently require GET requests with a JSON body rather than embedded params in the URL. You can achieve this via curl -X GET -H "Content-type: application/json" -H "Accept: application/json" -d \'{"text":"Some Text", "threshold": 0.5, "model": "opensearch"}\' "http://[ALEGRE_HOST]/text/similarity"')
    @api.doc(params={'text': 'text to be stored or queried for similarity', 'threshold': 'minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)', 'model': 'similarity model to use: "opensearch" (pure Elasticsearch, default) or the key name of an active model'})
    def post(self, similarity_type):
        args = request.json
        app.logger.debug(f"Args are {args}")
        for key in ["context", "models", "per_model_threshold", "vector"]:
            if args and args.get(key) and isinstance(args.get(key), str):
                args[key] = json.loads(args.get(key))
        if similarity_type == "text":
            package = similarity.get_body_for_text_document(args, 'query')
        else:
            app.logger.warning("Got to setting package...")
            package = similarity.get_body_for_media_document(args, 'query')
            app.logger.warning(f"Package is: {package}")
        return similarity.blocking_get_similar_items(package, similarity_type)
