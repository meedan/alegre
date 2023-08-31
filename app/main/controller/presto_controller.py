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
        data = request.args or request.json
        if action == "add_item":
            return similarity.callback_add_item(data, model_type)
        elif action == "search_item":
            return similarity.callback_get_similar_items(data, model_type)
        else:
            abort(404, description=f"Action type of {action} was not found. Currently available action types are add_item, search_item.")
