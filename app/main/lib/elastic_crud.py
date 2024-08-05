import pathlib
import os
import copy
import uuid
import urllib.error
import json
import tenacity
from flask import current_app as app
from app.main.lib.presto import Presto, PRESTO_MODEL_MAP
from app.main.lib.similarity_helpers import drop_context_from_record
from app.main.lib.helpers import merge_dict_lists
from app.main.lib import media_crud
from app.main.lib.elasticsearch import generate_matches, truncate_query, store_document, delete_document, update_or_create_document, get_by_doc_id

def _after_log(retry_state):
  app.logger.debug("Retrying image similarity...")

def delete(task, model):
    if task.get("doc_id"):
        deleted = delete_document(task.get("doc_id"), task.get("context"), quiet)
        return {"requested": task, "result": {"deleted": deleted}}
    else:
        return {"requested": task, "result": {"deleted": False}}

def get_object_by_doc_id(doc_id):
    return get_by_doc_id(doc_id)

def get_object(task, model):
    doc_id = task.get("doc_id", None)
    language = task.get("language", None)
    context = task.get("context", {})
    if context:
      task["contexts"] = [context]
    store_document(task, doc_id, language)
    if task.get("content") and not task.get("text"):
        task["text"] = task["content"]
    return task, False

def get_context_for_search(task):
    context = {}
    dup = copy.deepcopy(task)
    if dup.get('context'):
        context = dup.get('context')
    if dup.get("match_across_content_types"):
        context.pop("content_type", None)
    return context

def get_presto_request_response(modality, callback_url, task):
    response = json.loads(Presto.send_request(app.config['PRESTO_HOST'], PRESTO_MODEL_MAP[modality], callback_url, task, False).text)
    assert response["message"] == "Message pushed successfully", f"Bad response message for {modality}, {callback_url}, {task} - response was {response}"
    assert response["queue"] in PRESTO_MODEL_MAP.values(), f"Unknown queue for {modality}, {callback_url}, {task} - response was {response}"
    assert isinstance(response["body"], dict), f"Bad body for {modality}, {callback_url}, {task} - response was {response}"
    return response

def requires_encoding(obj):
    for model_key in obj.get("models", []):
        if not obj.get('model_'+model_key):
            return True
    return False

def get_blocked_presto_response(task, model, modality):
    if task.get("doc_id") is None:
        task["doc_id"] = str(uuid.uuid4())
    obj, temporary = get_object(task, model)
    doc_id = obj["doc_id"]
    callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], modality)
    app.logger.info(f"Object for {task} of model {model} with id of {doc_id} has requires_encoding value of {requires_encoding(obj)}")
    if requires_encoding(obj):
        blocked_results = []
        for model_key in obj.pop("models", []):
            if model_key != "elasticsearch" and not obj.get('model_'+model_key):
                response = get_presto_request_response(model_key, callback_url, obj)
                blocked_results.append(Presto.blocked_response(response, modality))
        # Warning: this is a blocking hold to wait until we get a response in 
        # a redis key that we've received something from presto.
        return obj, temporary, get_context_for_search(task), blocked_results[-1]
    else:
        return obj, temporary, get_context_for_search(task), {"body": obj}

def get_async_presto_response(task, model, modality):
    app.logger.error(f"get_async_presto_response: {task} {model} {modality}")
    obj, temporary = get_object(task, model)
    callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], modality)
    if task.get("doc_id") is None:
        task["doc_id"] = str(uuid.uuid4())
    task["final_task"] = "search"
    if requires_encoding(obj):
        responses = []
        for model_key in obj.get("models", []):
            if model_key != "elasticsearch" and not obj.get('model_'+model_key):
                task["model"] = model_key
                responses.append(get_presto_request_response(model_key, callback_url, task))
        return responses, True
    else:
        return {"message": "Already encoded - passing on to search"}, False

def parse_task_search(task):
    # here, we have to unpack the task contents to pull out the body,
    # which may be embedded in a body key in the dict if its coming from a presto callback.
    # alternatively, the "body" is just the entire dictionary.
    if "body" in task:
        body = task.get("body", {})
        threshold = task.get("raw", {}).get('threshold', 0.0)
        limit = body.get("raw", {}).get("limit")
        if not body.get("raw"):
            body["raw"] = {}
        body["hash_value"] = body.get("result", {}).get("hash_value")
        body["context"] = body.get("context", body.get("raw", {}).get("context"))
    else:
        body = task
        threshold = body.get('threshold', 0.0)
        limit = body.get("limit")
    return body, threshold, limit