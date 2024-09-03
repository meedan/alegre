import os
import json
from google.oauth2 import service_account
from flask import current_app as app

def get_credentialed_google_client(client):
    default_values = {}
    credentials_dict = {}
    if os.path.exists('./google_credentials.json'):
      with open('./google_credentials.json') as f:
        default_values = json.load(f)
      credentials_dict = {
        "type": os.getenv("google_credentials_type", default_values.get("type")),
        "project_id": os.getenv("google_credentials_project_id", default_values.get("project_id")),
        "private_key_id": os.getenv("google_credentials_private_key_id", default_values.get("private_key_id")),
        "private_key": os.getenv("google_credentials_private_key", default_values.get("private_key")).replace('\\n', '\n'),
        "client_email": os.getenv("google_credentials_client_email", default_values.get("client_email")),
        "client_id": os.getenv("google_credentials_client_id", default_values.get("client_id")),
        "auth_uri": os.getenv("google_credentials_auth_uri", default_values.get("auth_uri")),
        "token_uri": os.getenv("google_credentials_token_uri", default_values.get("token_uri")),
        "auth_provider_x509_cert_url": os.getenv("google_credentials_auth_provider_x509_cert_url", default_values.get("auth_provider_x509_cert_url")),
        "client_x509_cert_url": os.getenv("google_credentials_client_x509_cert_url", default_values.get("client_x509_cert_url")),
      }
    try:
      credentials = service_account.Credentials.from_service_account_info(credentials_dict)
      return client(credentials=credentials)
    except ValueError as e:
      print(f"Couldn't authenticate to google client: {str(e)}")
      return None
def convert_text_annotation_to_json(text_annotation):
    try:
        text_json = {}
        text_json['description'] = text_annotation.description
        text_json['locale'] = text_annotation.locale
        text_json['bounding_poly'] = []
        for a_vertice in text_annotation.bounding_poly.vertices:
            vertice_json = {}
            vertice_json['x'] = a_vertice.x
            vertice_json['y'] = a_vertice.y
            text_json['bounding_poly'] += [vertice_json]
        text_json = json.dumps(text_json)
        return text_json
    except:
        pass
