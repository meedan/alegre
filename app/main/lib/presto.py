import os
import json
import uuid
from flask import current_app as app
import requests
from app.main.lib.serializer import safe_serializer
from app.main.lib import redis_client
PRESTO_MODEL_MAP = {
    "audio": "audio__Model",
    "video": "video__Model",
    "image": "image__Model",
    "meantokens": "mean_tokens__Model",
    "indiansbert": "indian_sbert__Model",
    "mdebertav3filipino": "fptg__Model",
    "xlm-r-bert-base-nli-stsb-mean-tokens": "mean_tokens__Model",
    "indian-sbert": "indian_sbert__Model",
    "paraphrase-filipino-mpnet-base-v2": "fptg__Model",
}
PRESTO_RESPONSE_TIMEOUT = os.getenv('PRESTO_RESPONSE_TIMEOUT', 120)

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
            "content_hash": message.get("content_hash"),
            "url": message.get("url"),
            "text": message.get("text"),
            "raw": message,
            "requires_callback": requires_callback
        }
        if message.get("doc_id"):
            data["id"] = message.get("doc_id")
        else:
            data["id"] = str(uuid.uuid4())
        headers = {"Content-Type": "application/json"}
        json_data = json.dumps(data, default=safe_serializer)
        return requests.post(f"{presto_host}/process_item/{model_key}", data=json_data, headers=headers)

    def blocked_response(message, model_type):
        r = redis_client.get_client()
        item_id = message.get("body", {}).get("id")
        app.logger.info(f"Waiting for presence of key with name '{model_type}_{item_id}'....")
        response = r.blpop(f"{model_type}_{item_id}", timeout=PRESTO_RESPONSE_TIMEOUT)
        if response:
            _, value = response
            return json.loads(value)
        else:
            app.logger.warning(f"Timeout reached while waiting for key '{model_type}_{item_id}'")
            return None
