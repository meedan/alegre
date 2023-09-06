import uuid
from flask import current_app as app
import requests

class CheckAPI:
    @staticmethod
    def return_storage_webhook(check_api_host, action, model_type, data):
        return requests.post(f"{check_api_host}/api/webhooks/alegre", json={
            "action": action,
            "model_type": model_type,
            "data": data,
        })