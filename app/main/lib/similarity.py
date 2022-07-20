from datetime import datetime
import logging
from flask import request, current_app as app
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.image_similarity import add_image, delete_image, search_image
from app.main.lib.text_similarity import add_text, delete_text, search_text
DEFAULT_SEARCH_LIMIT = 20
logging.basicConfig(level=logging.INFO)
def get_body_for_text_document(params):
    models = set()
    if 'model' in params:
        models.add(params['model'])
    if 'models' in params:
        models = models|set(params['models'])
    if not models:
        models = ['elasticsearch']
    body = {'content': params.get('text'), 'created_at': params.get("created_at", datetime.now()), 'limit': params.get("limit", DEFAULT_SEARCH_LIMIT), 'models': list(models)}
    for key in ['context', 'threshold', 'fuzzy']:
        if key in params:
            body[key] = params[key]
    return body

def audio_model():
  return SharedModel.get_client(app.config['AUDIO_MODEL'])

def video_model():
  return SharedModel.get_client(app.config['VIDEO_MODEL'])

def model_response_package(item, command):
  response_package = {
    "limit": item.get("limit", similarity.DEFAULT_SEARCH_LIMIT) or similarity.DEFAULT_SEARCH_LIMIT,
    "url": item.get("url"),
    "doc_id": item.get("doc_id"),
    "context": item.get("context", {}),
    "created_at": item.get("created_at"),
    "command": command,
    "threshold": item.get("threshold", 0.0),
    "match_across_content_types": item.get("match_across_current_type", False)
  }
  app.logger.info(f"[Alegre Similarity] [Item {item}, Command {command}] Response package looks like {response_package}")
  return response_package

def add_item(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] Adding item")
  if similarity_type == "audio":
    response = audio_model().get_shared_model_response(model_response_package(item, "add"))
  elif similarity_type == "video":
    response = video_model().get_shared_model_response(model_response_package(item, "add"))
  elif similarity_type == "image":
    response = add_image(item)
  elif similarity_type == "text":
    doc_id = item.pop("doc_id", None)
    response = add_text(item, doc_id)
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for delete was {response}")
  return response

def delete_item(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] Deleting item")
  if similarity_type == "audio":
    response = audio_model().get_shared_model_response(model_response_package(item, "delete"))
  elif similarity_type == "video":
    response = video_model().get_shared_model_response(model_response_package(item, "delete"))
  elif similarity_type == "image":
    response = delete_image(item)
  elif similarity_type == "text":
    response = delete_text(item.get("doc_id"), item.get("quiet", False))
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for delete was {response}")
  return response

def get_similar_items(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] searching on item")
  if similarity_type == "audio":
    response = audio_model().get_shared_model_response(model_response_package(item, "search"))
  elif similarity_type == "video":
    response = video_model().get_shared_model_response(model_response_package(item, "search"))
  elif similarity_type == "image":
    response = search_image(item)
  elif similarity_type == "text":
    response = search_text(item)
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
  return response

