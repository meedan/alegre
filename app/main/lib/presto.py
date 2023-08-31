from flask import current_app as app
import requests

class Presto:
    @staticmethod
    def send_request(presto_host, model_key, callback_url, message):
        return requests.post(f"{presto_host}/process_item/{model_key}", json={
            "callback_url": callback_url,
            "id": message.get("doc_id"),
            "url": message.get("url"),
            "text": message.get("text"),
            "raw": message
        })