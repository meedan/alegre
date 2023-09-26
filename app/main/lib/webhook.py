import uuid
from flask import current_app as app
import requests

class Webhook:
    @staticmethod
    def return_storage_webhook(host, action, model_type, data):
        webhook_token = app.config['WEBHOOK_TOKEN']
        request = requests.post(f"{host}/api/webhooks/alegre?token={webhook_token}", json={
            "action": action,
            "model_type": model_type,
            "data": data,
        })
        return request