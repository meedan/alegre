import json
import uuid
import redis
from flask import current_app as app
import requests
from app.main.lib.serializer import safe_serializer
PRESTO_MODEL_MAP = {
    "audio": "audio__Model",
    "video": "video__Model",
    "image": "image__Model",
    "meantokens": "mean_tokens__Model",
    "indiansbert": "indian_sbert__Mode",
    "mdebertav3filipino": "fptg__Model",
}

class Presto:
    @staticmethod
    def add_item_callback_url(alegre_host, similarity_type):
        return f"{alegre_host}/presto/receive/add_item/{similarity_type}"

    @staticmethod
    def get_similar_items_callback_url(alegre_host, similarity_type):
        return f"{alegre_host}/presto/receive/search_item/{similarity_type}"

    @staticmethod
    def send_request(presto_host, model_key, callback_url, message, requires_callback=True):
        data = {
            "callback_url": callback_url,
            "id": message.get("doc_id", str(uuid.uuid4())),
            "url": message.get("url"),
            "text": message.get("text"),
            "raw": message,
            "requires_callback": requires_callback
        }
        headers = {"Content-Type": "application/json"}
        json_data = json.dumps(data, default=safe_serializer)
        return requests.post(f"{presto_host}/process_item/{model_key}", data=json_data, headers=headers)

    @staticmethod
    def blocked_response(message, model_type):
        r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
        item_id = message.get("body", {}).get("id")
        app.logger.error(f"Waiting for present of key with name '{model_type}_{item_id}'....")
        _, value = r.blpop(f"{model_type}_{item_id}")
        return json.loads(value)
