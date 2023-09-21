import uuid
from flask import current_app as app
import requests

class CheckAPI:
    @staticmethod
    def return_storage_webhook(check_api_host, action, model_type, data):
        check_api_token = app.config['CHECK_API_TOKEN']
        request = requests.post(f"{check_api_host}/api/webhooks/alegre?token={check_api_token}", json={
            "action": action,
            "model_type": model_type,
            "data": data,
        })
        return request