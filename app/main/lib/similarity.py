import json
from datetime import datetime
import logging
from flask import request, current_app as app
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.shared_models.audio_model import AudioModel
from app.main.lib.presto import Presto, PRESTO_MODEL_MAP
from app.main.lib.image_similarity import add_image, callback_add, delete_image, blocking_search_image, async_search_image, async_search_image_on_callback
from app.main.lib.text_similarity import add_text, delete_text, search_text
DEFAULT_SEARCH_LIMIT = 200
logging.basicConfig(level=logging.INFO)
def get_body_for_media_document(params, mode):
    """
      This function should only be called when querying or storing a media object.
      @params mode should be "query" or "store"
      If we are querying for a document, use a permissive approach and keep all params
      with some reformating. If we are storing, we remove unexpected items in
      `params` in order to avoid things being stored in OpenSearch unintentionally
    """
    app.logger.info(
    f"[Alegre Similarity] get_body_for_text_document (mode={mode}):params (start) {params}")
    if 'created_at' not in params:
      params['created_at'] = datetime.now()
    if 'limit' not in params:
      params['limit'] = DEFAULT_SEARCH_LIMIT
    return params

def get_body_for_text_document(params, mode):
    """
      This function should only be called when querying or storing a
      document in OpenSearch.
      @params mode should be "query" or "store"
      If we are querying for a document, use a permissive approach and keep all params
      with some reformating. If we are storing, we remove unexpected items in
      `params` in order to avoid things being stored in OpenSearch unintentionally
    """
    app.logger.info(
    f"[Alegre Similarity] get_body_for_text_document (mode={mode}):params (start) {params}")

    # Combine model and models
    models = set()
    if 'model' in params:
        models.add(params['model'])
        del params['model']
    if 'models' in params:
        models = models|set(params['models'])
    if not models:
        models = ['elasticsearch']
    params['models'] = list(models)

    # Rename "text" to "content" if present
    if 'text' in params:
      params['content'] = params.get('text')
      del params["text"]

    # Set defaults
    if 'created_at' not in params:
      params['created_at'] = datetime.now()
    if 'limit' not in params:
      params['limit'] = DEFAULT_SEARCH_LIMIT
    if 'language' not in params:
      params['language'] = None
    if 'content' not in params:
      params['content'] = None

    if mode == 'store':
      allow_list = set(['language', 'content', 'created_at', 'models', 'context', 'callback_url'])
      keys_to_remove = params.keys() - allow_list
      app.logger.info(
        f"[Alegre Similarity] get_body_for_text_document:running in `store' mode. Removing {keys_to_remove}")
      for key in keys_to_remove:
        del params[key]
    app.logger.info(
      f"[Alegre Similarity] get_body_for_text_document (mode={mode}):params (end) {params}")
    return params

def audio_model():
  return AudioModel(app.config['AUDIO_MODEL'])

def video_model():
  return SharedModel.get_client(app.config['VIDEO_MODEL'])

def model_response_package(item, command):
  response_package = {
    "limit": item.get("limit", DEFAULT_SEARCH_LIMIT) or DEFAULT_SEARCH_LIMIT,
    "url": item.get("url"),
    "callback_url": item.get("callback_url"),
    "doc_id": item.get("doc_id"),
    "context": item.get("context", {}),
    "created_at": item.get("created_at"),
    "command": command,
    "threshold": item.get("threshold", 0.0),
    "per_model_threshold": item.get("per_model_threshold", {}),
    "match_across_content_types": item.get("match_across_current_type", False),
    "confirmed": item.get("confirmed", False),
    "requires_callback": item.get("requires_callback", False)
  }
  app.logger.info(f"[Alegre Similarity] [Item {item}, Command {command}] Response package looks like {response_package}")
  return response_package

def add_item(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] Adding item")
  callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], similarity_type)
  if similarity_type == "audio":
    response = Presto.send_request(app.config['PRESTO_HOST'], PRESTO_MODEL_MAP[similarity_type], callback_url, model_response_package(item, "add")).text
    response = json.loads(response)
  elif similarity_type == "video":
    response = video_model().get_shared_model_response(model_response_package(item, "add"))
  elif similarity_type == "image":
    response = add_image(item)
  elif similarity_type == "text":
    doc_id = item.pop("doc_id", None)
    language = item.pop("language", None)
    response = add_text(item, doc_id, language)
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for add was {response}")
  return response

def callback_add_item(item, similarity_type):
  if similarity_type == "audio":
      response = audio_model().add(item)
      app.logger.info(f"[Alegre Similarity] CallbackAddItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
  if similarity_type == "video":
      response = video_model().add(item)
      app.logger.info(f"[Alegre Similarity] CallbackAddItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
  if similarity_type == "image":
      response = callback_add(item)
      app.logger.info(f"[Alegre Similarity] CallbackAddItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
  else:
      app.logger.warning(f"[Alegre Similarity] InvalidCallbackAddItem: [Item {item}, Similarity type: {similarity_type}] No response")
  return response

def callback_search_item(item, similarity_type):
  if similarity_type == "audio":
      response = audio_model().search(model_response_package(item, "search"))
      app.logger.info(f"[Alegre Similarity] CallbackAddItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
  elif similarity_type == "video":
      response = video_model().search(model_response_package(item, "search"))
      app.logger.info(f"[Alegre Similarity] CallbackAddItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
  elif similarity_type == "image":
      response = async_search_image_on_callback(item)
      app.logger.info(f"[Alegre Similarity] CallbackAddItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
  else:
      app.logger.warning(f"[Alegre Similarity] InvalidCallbackAddItem: [Item {item}, Similarity type: {similarity_type}] No response")
  return {"item": item, "results": response}

def delete_item(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] Deleting item")
  if similarity_type == "audio":
    response = audio_model().delete(model_response_package(item, "delete"))
  elif similarity_type == "video":
    response = video_model().get_shared_model_response(model_response_package(item, "delete"))
  elif similarity_type == "image":
    response = delete_image(item)
  elif similarity_type == "text":
    response = delete_text(item.get("doc_id"), item.get("context", {}), item.get("quiet", False))
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for delete was {response}")
  return response

def get_similar_items(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] searching on item")
  response = None
  if similarity_type == "video":
    response = video_model().get_shared_model_response(model_response_package(item, "search"))
  elif similarity_type == "text":
    response = search_text(item)
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
  return response

def blocking_get_similar_items(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] searching on item")
  if similarity_type == "audio":
    response = audio_model().blocking_search(model_response_package(item, "search"), "audio")
    app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
    return response
  elif similarity_type == "image":
    response = blocking_search_image(item)
    app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
    return response
  else:
      raise Exception(f"{similarity_type} modality not implemented for blocking requests!")

def async_get_similar_items(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] searching on item")
  if similarity_type == "audio":
    response = audio_model().async_search(model_response_package(item, "search"), "audio")
    app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
    return response
  elif similarity_type == "video":
    response = video_model().async_search(model_response_package(item, "search"), "video")
    app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
    return response
  elif similarity_type == "image":
    response = async_search_image(item, "image")
    app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
    return response
  else:
      raise Exception(f"{similarity_type} modality not implemented for async requests!")

