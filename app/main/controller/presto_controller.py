from flask import request, current_app as app
from flask_restplus import Resource, Namespace
import json

from app.main.lib.fields import JsonObject
from app.main.lib import similarity
from app.main.lib.webhook import Webhook
from app.main.lib import redis_client

api = Namespace('presto', description='presto callback url')
presto = api.model('presto', {
    'body': JsonObject(
        required=False,
        description='Original body of the message sent - will contain ID, callback_url, and original url/text of request'
    ),
    'response': JsonObject(
        required=False,
        description='The response data sent back from the model'
    ),
})
@api.route('/receive/<string:action>/<string:model_type>')
class PrestoResource(Resource):
    @api.response(200, 'Successfully responded to presto callback.')
    @api.doc('Receive a presto callback for a given `model_type`')
    def post(self, action, model_type):
        data = request.json
        item_id = data.get("body", {}).get("id")
        app.logger.info(f"PrestoResource {action}/{model_type}, data is {data}")
        return_value = None
        if action == "add_item":
            result = similarity.callback_add_item(data.get("body"), model_type)
            if data.get("body", {}).get("raw", {}).get("suppress_response"):
                # requested not to reply to caller with similarity response, so suppress it
                return_value = {"action": action, "model_type": model_type, "data": result}
            else:
                if data.get("body", {}).get("raw", {}).get("final_task") == "search":
                # compute a set of items that are similar to the just-stored item and respond to caller with them
                    result = similarity.callback_search_item(data.get("body"), model_type)
                    if result:
                        result["is_search_result_callback"] = True
                callback_url = data.get("body", {}).get("raw", {}).get("callback_url", app.config['CHECK_API_HOST']) or app.config['CHECK_API_HOST']
                if result and result.get("results") is not None and data.get("body", {}).get("raw", {}).get("requires_callback"):
                    app.logger.info(f"Sending callback to {callback_url} for {action} for model of {model_type} with body of {result}")
                    Webhook.return_webhook(callback_url, action, model_type, result)
                return_value = {"action": action, "model_type": model_type, "data": result}
                app.logger.info(f"PrestoResource {action}/{model_type}, data is {data}, return_value is {return_value}")
        r = redis_client.get_client()
        r.lpush(f"{model_type}_{item_id}", json.dumps(data))
        r.expire(f"{model_type}_{item_id}", 60*60*24)
        if return_value:
            return return_value
        else:
            abort(
                404,
                description=f"Action type of {action} was not found. Currently available action types are add_item, search_item."
            )
