from flask import request, current_app as app
from flask_restplus import Resource, Namespace

from app.main.lib.fields import JsonObject
from app.main.lib import similarity

api = Namespace('presto', description='presto callback url')
presto = api.model('presto', {
    'body': JsonObject(required=False, description='Original body of the message sent - will contain ID, callback_url, and original url/text of request'),
    'response': JsonObject(required=False, description='The response data sent back from the model'),
})
@api.route('/receive/<string:action>/<string:model_type>')
class PrestoResource(Resource):
    @api.response(200, 'Successfully responded to presto callback.')
    @api.doc('Receive a presto callback for a given `model_type`')
    def post(self, action, model_type):
        if action == "add":
            return similarity.add_item(request.args or request.json, model_type)
        elif action == "search":
            return similarity.get_similar_items(request.args or request.json, model_type)