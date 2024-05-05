import pathlib
import os
import copy
import uuid
import urllib.error
import json
import tenacity
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.attributes import flag_modified
from flask import current_app as app
from app.main import db
from app.main.model.video import Video
from app.main.lib.presto import Presto, PRESTO_MODEL_MAP
from app.main.lib.similarity_helpers import drop_context_from_record

def merge_dict_lists(list1, list2):
    """
    Merge two lists of dictionaries, ensuring all unique dictionaries are present in the final result.
    
    :param list1: First list of dictionaries.
    :param list2: Second list of dictionaries.
    :return: Merged list of unique dictionaries.
    """
    def to_hashable(d):
        return tuple((k, tuple(v) if isinstance(v, list) else v) for k, v in sorted(d.items()))
    def to_dict(t):
        return {k: list(v) if isinstance(v, tuple) else v for k, v in t}
    unique = set(to_hashable(d) for d in list1 + list2)
    return [to_dict(d) for d in unique]

def _after_log(retry_state):
  app.logger.debug("Retrying image similarity...")

def tmk_file_path(folder, filepath, create_path=True):
    directory = app.config['PERSISTENT_DISK_PATH']
    if create_path:
        pathlib.Path(f"{directory}/{folder}").mkdir(parents=True, exist_ok=True)
    return f"{directory}/{folder}/{filepath}.tmk"

@tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
def save(obj, model, modifiable_fields=[]):
    try:
        # First locate existing media and append new context
        existing = db.session.query(model).filter(model.url==obj.url).one()
        if existing:
            for field in modifiable_fields:
                if getattr(obj, field) is not None  and not getattr(existing, field):
                    setattr(existing, field, getattr(obj, field))
                    flag_modified(existing, field)
                if isinstance(obj.context, list):
                    existing.context = merge_dict_lists(obj.context, existing.context)
                    flag_modified(existing, 'context')
                elif isinstance(obj.context, dict) and obj.context not in existing.context:
                    existing.context.append(obj.context)
                    flag_modified(existing, 'context')
            saved_obj = existing
    except NoResultFound as e:
        # Otherwise, add new audio, but with context as an array
        if obj.context and not isinstance(obj.context, list):
            obj.context = [obj.context]
        db.session.add(obj)
        saved_obj = obj
    except Exception as e:
        db.session.rollback()
        raise e
    try:
        db.session.commit()
        return saved_obj
    except Exception as e:
        db.session.rollback()
        raise e
    return saved_obj

def delete(task, model):
    deleted = False
    obj = get_by_doc_id_or_url(task, model)
    if obj:
        if task["context"] in obj.context and len(obj.context) > 1:
            deleted = drop_context_from_record(obj, task.get("context", {}))
        else:
            if isinstance(obj, Video):
                filepath = tmk_file_path(obj.folder, obj.filepath)
                if os.path.exists(filepath):
                    os.remove(filepath)
            deleted = db.session.query(model).filter(model.id==obj.id).delete()
        db.session.commit()
        return {"requested": task, "result": {"url": obj.url, "deleted": deleted}}
    else:
        return {"requested": task, "result": {"url": task.get("url"), "deleted": False}}

def add(task, model, modifiable_fields=[]):
    obj = model.from_task_data(task, get_by_doc_id_or_url(task, model))
    try:
        obj = save(obj, model, modifiable_fields)
    except sqlalchemy.exc.IntegrityError:
        app.logger.error(f"sqlalchemy.exc.IntegrityError! Failed to store obj of {model} for task of {task} with modifiable fields of {modifiable_fields}!")
        obj = None
    if obj:
        return {"requested": task, "result": {"url": obj.url}, "success": True}, obj
    else:
        return {"requested": task, "result": {"url": task.get("url")}, "success": False}, None

def get_by_doc_id_or_url(task, model):
    obj = None
    if 'doc_id' in task:
        objs = db.session.query(model).filter(model.doc_id==task.get("doc_id")).all()
        if objs:
            obj = objs[0]
    if 'url' in task:
        objs = db.session.query(model).filter(model.url==task.get("url")).all()
        if objs:
            obj = objs[0]
    return obj

def get_object(task, model):
    temporary = False
    obj = get_by_doc_id_or_url(task, model)
    if obj is None:
        temporary = True
        if not task.get("doc_id"):
            task["doc_id"] = str(uuid.uuid4())
        add(task, model)
        obj = get_by_doc_id_or_url(task, model)
    return obj, temporary

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

def ensure_context_appended(task, existing):
    context = task.get("context", task.get("raw", {}).get("context"))
    if isinstance(context, list):
      existing.context = [dict(t) for t in set(tuple(sorted(d.items())) for d in context + existing.context)]
      flag_modified(existing, 'context')
    elif isinstance(context, dict) and context not in existing.context:
      existing.context.append(context)
      flag_modified(existing, 'context')
    return existing

def get_blocked_presto_response(task, model, modality):
    obj, temporary = get_object(task, model)
    obj = ensure_context_appended(task, obj)
    callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], modality)
    if task.get("doc_id") is None:
        task["doc_id"] = str(uuid.uuid4())
    app.logger.error(f"Object for {task} of model {model} with id of {obj.id} has requires_encoding value of {obj.requires_encoding}")
    if obj.requires_encoding:
        response = get_presto_request_response(modality, callback_url, task)
        # Warning: this is a blocking hold to wait until we get a response in 
        # a redis key that we've received something from presto.
        return obj, temporary, get_context_for_search(task), Presto.blocked_response(response, modality)
    else:
        return obj, temporary, get_context_for_search(task), obj.existing_response

def get_async_presto_response(task, model, modality):
    obj, temporary = get_object(task, model)
    context = [get_context_for_search(task)]
    callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], modality)
    if task.get("doc_id") is None:
        task["doc_id"] = str(uuid.uuid4())
    task["final_task"] = "search"
    if obj.requires_encoding:
        response = get_presto_request_response(modality, callback_url, task)
        return response, True
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