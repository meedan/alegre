import json
from datetime import datetime
import logging
from flask import request, current_app as app
from app.main.lib.shared_models.audio_model import AudioModel
from app.main.lib.shared_models.video_model import VideoModel
from app.main.lib.presto import Presto, PRESTO_MODEL_MAP
from app.main.lib.image_similarity import add_image, callback_add_image, delete_image, blocking_search_image, async_search_image, async_search_image_on_callback
from app.main.lib.text_similarity import add_text, async_search_text, async_search_text_on_callback, callback_add_text, delete_text, search_text
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
      allow_list = set(['language', 'content', 'created_at', 'models', 'context', 'callback_url', 'content_hash'])
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
  return VideoModel(app.config['VIDEO_MODEL'])

def model_response_package(item, command):
  response_package = {
    "limit": item.get("limit", DEFAULT_SEARCH_LIMIT) or DEFAULT_SEARCH_LIMIT,
    "url": item.get("url"),
    "callback_url": item.get("callback_url"),
    "content_hash": item.get("content_hash"),
    "doc_id": item.get("doc_id"),
    "context": item.get("context", {}),
    "created_at": item.get("created_at"),
    "command": command,
    "threshold": item.get("threshold", 0.0),
    "per_model_threshold": item.get("per_model_threshold", {}),
    "match_across_content_types": item.get("match_across_current_type", True),
    "confirmed": item.get("confirmed", False),
    "requires_callback": item.get("requires_callback", False)
  }
  for optional_key in ["folder", "filepath"]:
      if optional_key in item.keys():
          response_package[optional_key] = item[optional_key]
  app.logger.info(f"[Alegre Similarity] [Item {item}, Command {command}] Response package looks like {response_package}")
  return response_package

def add_item(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] Adding item")
  callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], similarity_type)
  if similarity_type == "audio":
    response = Presto.send_request(app.config['PRESTO_HOST'], PRESTO_MODEL_MAP[similarity_type], callback_url, model_response_package(item, "add")).text
    response = json.loads(response)
  elif similarity_type == "video":
    response = Presto.send_request(app.config['PRESTO_HOST'], PRESTO_MODEL_MAP[similarity_type], callback_url, model_response_package(item, "add")).text
    response = json.loads(response)
  elif similarity_type == "image":
    response = add_image(item)
  elif similarity_type == "text":
    doc_id = item.pop("doc_id", None)
    language = item.pop("language", None)
    response = add_text(item, doc_id, language)
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for add was {response}")
  return response

def callback_add_item(item, similarity_type):
    function = None
    if similarity_type == "audio":
        function = audio_model().add
    elif similarity_type == "video":
        function = video_model().add
    elif similarity_type == "image":
        function = callback_add_image
    elif similarity_type == "text":
        function = callback_add_text
    if function:
        response = function(item)
        app.logger.info(f"[Alegre Similarity] CallbackAddItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
        return response
    else:
        app.logger.warning(f"[Alegre Similarity] InvalidCallbackAddItem: [Item {item}, Similarity type: {similarity_type}] No response")

def merge_audio_and_video_responses(video_response, audio_response):
    full_responses = []
    for result_set in [video_response["result"], audio_response["result"]]:
        for result in result_set:
            full_responses.append(result)
    full_responses.sort(key=lambda x: x['score'], reverse=True)
    return {"result": full_responses}

def callback_search_item(item, similarity_type):
  if similarity_type == "audio":
      response = audio_model().search(model_response_package(item.get("raw"), "search"))
      app.logger.info(f"[Alegre Similarity] CallbackSearchItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
  elif similarity_type == "video":
      response = video_model().search(model_response_package(item.get("raw"), "search"))
      # When we search for a video, we need to also search for the audio track of the video against our audio library in case it matches other audio clips.
      # audio_response = audio_model().search(video_model().overload_context_to_denote_content_type(model_response_package(item.get("raw"), "search")))
      # response = merge_audio_and_video_responses(video_response, audio_response)
      app.logger.info(f"[Alegre Similarity] CallbackSearchItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
  elif similarity_type == "image":
      response = async_search_image_on_callback(item)
      app.logger.info(f"[Alegre Similarity] CallbackSearchItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
  elif similarity_type == "text":
      response = async_search_text_on_callback(item)
      app.logger.info(f"[Alegre Similarity] CallbackSearchItem: [Item {item}, Similarity type: {similarity_type}] Response looks like {response}")
  else:
      app.logger.warning(f"[Alegre Similarity] InvalidCallbackSearchItem: [Item {item}, Similarity type: {similarity_type}] No response")
  return {"item": item, "results": response}

def delete_item(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] Deleting item")
  if similarity_type == "audio":
    response = audio_model().delete(model_response_package(item, "delete"))
  elif similarity_type == "video":
    response = video_model().delete(model_response_package(item, "delete")) # Changed Since 4126 PR
  elif similarity_type == "image":
    response = delete_image(item)
  elif similarity_type == "text":
    response = delete_text(item.get("doc_id"), item.get("context", {}), item.get("quiet", False))
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for delete was {response}")
  return response

def get_similar_items(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] searching on item")
  response = None
  if similarity_type == "text":
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
  elif similarity_type == "video":
    response = video_model().blocking_search(model_response_package(item, "search"), "video")
    app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
    return response
  else:
      raise Exception(f"{similarity_type} modality not implemented for blocking requests!")

def async_get_similar_items(item, similarity_type):
  app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] searching on item")
  if similarity_type == "audio":
    response, waiting_for_callback = audio_model().async_search(model_response_package(item, "search"), "audio")
    app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
    return response, waiting_for_callback
  elif similarity_type == "video":
    response, waiting_for_callback = video_model().async_search(model_response_package(item, "search"), "video")
    # Searching with an audio_model() call here is intentional - we need to encode the audio
    # track for all videos to see if we can match them across modes (i.e. this MP3 matches
    # this video's audio track, so they are able to be matched)
    # _, waiting_for_audio_callback = audio_model().async_search(video_model().overload_context_to_denote_content_type(model_response_package(item, "search")), "audio")
    app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
    return response, waiting_for_callback# or waiting_for_audio_callback
  elif similarity_type == "image":
    response, waiting_for_callback = async_search_image(item, "image")
    app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
    return response, waiting_for_callback
  elif similarity_type == "text":
    response, waiting_for_callback = async_search_text(item, "text")
    app.logger.info(f"[Alegre Similarity] [Item {item}, Similarity type: {similarity_type}] response for search was {response}")
    return response, waiting_for_callback
  else:
      raise Exception(f"{similarity_type} modality not implemented for async requests!")