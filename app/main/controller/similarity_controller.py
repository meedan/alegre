import json
from flask import request, current_app as app
from flask import abort
from flask_restplus import Resource, Namespace, fields

from app.main.lib.fields import JsonObject
from app.main.lib import similarity

api = Namespace('similarity', description='text similarity operations')
similarity_request = api.model('similarity_request', {
    'text': fields.String(required=False, description='text to be stored or queried for similarity'),
    'doc_id': fields.String(required=False, description='text ID to constrain uniqueness'),
    'model': fields.String(required=False, description='similarity model to use: "elasticsearch" (pure Elasticsearch, default) or the key name of an active model'),
    'models': fields.List(required=False, description='similarity models to use: ["elasticsearch"] (pure Elasticsearch, default) or the key name of an active model', cls_or_instance=fields.String),
    'language': fields.String(required=False, description='language code for the analyzer to use during the similarity query (defaults to standard analyzer)'),
    'threshold': fields.Float(required=False, description='minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)'),
    'context': JsonObject(required=False, description='context'),
    'fuzzy': fields.Boolean(required=False, description='whether or not to use fuzzy search on GET queries (only used when model is set to \'elasticsearch\')'),
})
@api.route('/')
class SimilarityResource(Resource):
    @api.response(200, 'text successfully deleted in the similarity database.')
    @api.doc('Delete a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def delete(self):
        doc_id = request.json.get("doc_id")
        response = similarity.delete_item(request.json, "text")
        if response == False:
            abort(404, description=f"Doc Not Found for id {doc_id}! No Deletion Occurred.")
        else:
            return response

    @api.response(200, 'text successfully stored in the similarity database.')
    @api.doc('Store a text in the similarity database')
    @api.expect(similarity_request, validate=True)
    def post(self):
        doc_id = request.json.get("doc_id")
        item = similarity.get_body_for_text_document(request.json, mode='store')
        item["doc_id"] = doc_id
        return similarity.add_item(item, "text")

@api.route('/search/')
class SimilaritySearchResource(Resource):
    @api.response(200, 'text similarity successfully queried.')
    @api.doc('Make a text similarity query. Note that we currently require GET requests with a JSON body rather than embedded params in the URL. You can achieve this via curl -X GET -H "Content-type: application/json" -H "Accept: application/json" -d \'{"text":"Some Text", "threshold": 0.5, "model": "elasticsearch"}\' "http://[ALEGRE_HOST]/text/similarity"')
    @api.doc(params={'text': 'text to be stored or queried for similarity', 'threshold': 'minimum score to consider, between 0.0 and 1.0 (defaults to 0.9)', 'model': 'similarity model to use: "elasticsearch" (pure Elasticsearch, default) or the key name of an active model'})
    def post(self):
      args = request.json
      app.logger.warning(f"Args are {args}")
      for key in ["context", "models", "per_model_threshold", "vector"]:
        if args and args.get(key) and isinstance(args.get(key), str):
          args[key] = json.loads(args.get(key))
      return similarity.get_similar_items(similarity.get_body_for_text_document(args, mode='query'), "text")
