from flask import request, current_app as app
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.image_similarity import add_image, delete_image, search_image
from app.main.lib.text_similarity import add_text, delete_text, search_text

def audio_model():
  return SharedModel.get_client(app.config['AUDIO_MODEL'])

def video_model():
  return SharedModel.get_client(app.config['VIDEO_MODEL'])

def model_response_package(item, command):
  return {
    "url": item.get("url"),
    "doc_id": item.get("doc_id"),
    "context": item.get("context", {}),
    "created_at": item.get("created_at"),
    "command": command,
    "threshold": item.get("threshold", 0.0),
    "match_across_content_types": item.get("match_across_current_type", False)
  }

def add_item(item, similarity_type):
  if similarity_type == "audio":
    return audio_model().get_shared_model_response(model_response_package(item, "add"))
  elif similarity_type == "video":
    return video_model().get_shared_model_response(model_response_package(item, "add"))
  elif similarity_type == "image":
    return add_image(item)
  elif similarity_type == "text":
    doc_id = item.pop("doc_id", None)
    return add_text(item, doc_id)

def delete_item(item, similarity_type):
  if similarity_type == "audio":
    return audio_model().get_shared_model_response(model_response_package(item, "delete"))
  elif similarity_type == "video":
    return video_model().get_shared_model_response(model_response_package(item, "delete"))
  elif similarity_type == "image":
    return save_image(item)
  elif similarity_type == "text":
    return delete_text(item.get("doc_id"), item.get("quiet", False))

def get_similar_items(item, similarity_type):
  if similarity_type == "audio":
    return audio_model().get_shared_model_response(model_response_package(item, "search"))
  elif similarity_type == "video":
    return video_model().get_shared_model_response(model_response_package(item, "search"))
  elif similarity_type == "image":
    return search_image(item)
  elif similarity_type == "text":
    return search_text(item)

