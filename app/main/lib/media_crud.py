import uuid
import urllib.error
import json
import tenacity
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.attributes import flag_modified
from flask import current_app as app
from app.main import db
from app.main.lib.presto import Presto, PRESTO_MODEL_MAP
def _after_log(retry_state):
  app.logger.debug("Retrying image similarity...")

@tenacity.retry(wait=tenacity.wait_fixed(0.5), stop=tenacity.stop_after_delay(5), after=_after_log)
def save(obj, model, modifiable_fields=[]):
    saved_object = None
    try:
        # First locate existing audio and append new context
        existing = db.session.query(model).filter(model.url==obj.url).one()
        if existing:
            for field in modifiable_fields:
                if obj.hash_value is not None  and not existing.hash_value:
                    setattr(existing, field, getattr(obj, field))
                    flag_modified(existing, field)
            if obj.context not in existing.context:
                existing.context.append(obj.context)
                flag_modified(existing, 'context')
            saved_obj = existing
    except NoResultFound as e:
        # Otherwise, add new audio, but with context as an array
        app.logger.debug(f"Adding {model} object that looks like "+str(obj.__dict__))
        if obj.context and not isinstance(obj.context, list):
            obj.context = [obj.context]
            app.logger.debug("Set context to "+str(obj.context))
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
        if task.get("context", {}) in obj.context and len(obj.context) > 1:
            deleted = drop_context_from_record(obj, task.get("context", {}))
        else:
            deleted = db.session.query(model).filter(model.id==obj.id).delete()
        return {"requested": task, "result": {"url": obj.url, "deleted": deleted}}
    else:
        return {"requested": task, "result": {"url": task.get("url"), "deleted": False}}

def add(task, model, modifiable_fields=[]):
    try:
        obj = model.from_task_data(task)
        try:
          obj = save(obj, model, modifiable_fields)
        except sqlalchemy.exc.IntegrityError:
          obj = None
        if obj:
          return {"requested": task, "result": {"url": obj.url}, "success": True}
        else:
          return {"requested": task, "result": {"url": task.get("url")}, "success": False}
    except urllib.error.HTTPError:
        return {"requested": task, "result": {"url": task.get("url")}, "success": False}

def get_by_doc_id_or_url(task, model):
    obj = None
    if 'doc_id' in task:
        objs = db.session.query(model).filter(model.doc_id==task.get("doc_id")).all()
        if objs:
            obj = objs[0]
    elif 'url' in task:
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
        app.logger.debug("Adding temporary audio object of "+str(task))
        add(task, model)
        obj = get_by_doc_id_or_url(task, model)
    return obj, temporary

def get_context_for_search(task):
    context = {}
    if task.get('context'):
        context = task.get('context')
    if task.get("match_across_content_types"):
        context.pop("content_type", None)
    context.pop("project_media_id", None)
    return context

def get_blocked_presto_response(task, model, modality):
    obj, temporary = get_object(task, model)
    context = get_context_for_search(task)
    callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], modality)
    if task.get("doc_id") is None:
        task["doc_id"] = str(uuid.uuid4())
    response = json.loads(Presto.send_request(app.config['PRESTO_HOST'], PRESTO_MODEL_MAP[modality], callback_url, task, False).text)
    # Warning: this is a blocking hold to wait until we get a response in 
    # a redis key that we've received something from presto.
    return obj, temporary, context, Presto.blocked_response(response, modality)

def get_async_presto_response(task, model, modality):
    obj, temporary = get_object(task, model)
    context = get_context_for_search(task)
    callback_url =  Presto.add_item_callback_url(app.config['ALEGRE_HOST'], modality)
    if task.get("doc_id") is None:
        task["doc_id"] = str(uuid.uuid4())
    task["final_task"] = "search"
    response = json.loads(Presto.send_request(app.config['PRESTO_HOST'], PRESTO_MODEL_MAP[modality], callback_url, task, False).text)
    if response:
        return response
    else:
        return {"error": f"{model} could not be sent for fingerprinting", "task": task}

