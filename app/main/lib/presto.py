import json
import uuid
import redis
from flask import current_app as app
import requests

class Presto:
    @staticmethod
    def add_item_callback_url(alegre_host, similarity_type):
        return f"{alegre_host}/presto/receive/add_item/{similarity_type}"

    @staticmethod
    def get_similar_items_callback_url(alegre_host, similarity_type):
        return f"{alegre_host}/presto/receive/search_item/{similarity_type}"

    @staticmethod
    def send_request(presto_host, model_key, callback_url, message):
        return requests.post(f"{presto_host}/process_item/{model_key}", json={
            "callback_url": callback_url,
            "id": message.get("doc_id", str(uuid.uuid4())),
            "url": message.get("url"),
            "text": message.get("text"),
            "raw": message
        })

    @staticmethod
    def blocked_response(message, model_type):
        r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
        id = message.get("body", {}).get("id")
        key, value = r.blpop(f"{model_type}_{id}")
        return json.loads(value)
