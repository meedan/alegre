import time
import json
import uuid
from datetime import datetime
from collections import namedtuple
import redis
import time
import importlib
import os
import hashlib
import re

from flask import current_app as app

Task = namedtuple('Task', 'task_id task_type task_package')

class SharedModel(object):
  @staticmethod
  def import_model_class(model_class):
    class_name = re.sub(r'(?<!^)(?=[A-Z])', '_', model_class).lower()
    return getattr(importlib.import_module('app.main.lib.shared_models.%s' % class_name), model_class)

  @staticmethod
  def start_server(model_class, model_key, options={}):
    class_ = SharedModel.import_model_class(model_class)
    instance = class_(model_key, options)
    instance.load()
    app.logger.info('[%s] Serving model...', model_key)
    r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
    r.set('SharedModel:%s' % model_key, json.dumps({
      'model_class': model_class,
      'model_key': model_key,
      'options': options
    }))
    r.sadd('SharedModel', model_key)
    instance.bulk_run()

  @staticmethod
  def get_servers():
    r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
    return [server.decode('utf-8') for server in r.smembers('SharedModel')]

  @staticmethod
  def get_client(model_key, options={}):
    r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
    model_info = r.get("SharedModel:%s" % model_key)
    assert model_info is not None, f"Unable locate model info for key {model_key}"
    model_class = json.loads(model_info.decode('utf-8'))['model_class']
    class_ = SharedModel.import_model_class(model_class)
    return class_(model_key, options)

  def __init__(self, model_key, options={}):
    self.options = options
    self.queue_name = model_key
    self.datastore = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])

  def get_task(self, timeout=0):
    item = self.datastore.blpop(self.queue_name, timeout)
    if item:
      task = Task(**json.loads(item[1].decode('utf-8')))
      app.logger.info('[%s] Picking up task %s', self.queue_name, task.task_id)
      return task

  def send_response(self, task, response):
    self.datastore.set(task.task_id, json.dumps({"response": response}))

  def run(self):
    while True:
      task = self.get_task()
      if task:
        self.send_response(
          task,
          self.respond(task.task_package)
        )

  def get_tasks(self):
    tasks = []
    start = datetime.now()
    while (datetime.now()-start).total_seconds() < 0.1 and len(tasks) < 50:
      task = self.get_task(1)
      if task:
        tasks.append(task)
    return tasks

  def bulk_run(self):
    while True:
      tasks = self.get_tasks()
      responses = ([self.respond(task.task_package) for task in tasks])
      for i, response in enumerate(responses):
        self.send_response(
          tasks[i],
          response
        )

  def task_id(self):
    return str(uuid.uuid4())

  def task_message(self, analysis_value):
    return Task(
      task_id=self.task_id(),
      task_type=self.queue_name,
      task_package=analysis_value
    )

  def submit_task(self, task):
    self.push_task(task)
    return task

  def encode_task(self, task):
    return json.dumps(task._asdict())

  def push_task(self, task):
    app.logger.info('[%s] Pushing task %s', self.queue_name, task.task_id)
    return self.datastore.rpush(
      task.task_type,
      self.encode_task(task)
    )

  def get_task_result(self, task):
    return self.datastore.get(task.task_id)

  def delete_task_response(self, task):
    return self.datastore.delete(task.task_id)

  def read_task_response(self, task):
    result = self.get_task_result(task)
    if result:
      return json.loads(
        result.decode('utf-8')
      )['response']

  def get_task_response(self, task, max_timeout=60):
    start = datetime.now()
    while (datetime.now()-start).total_seconds() < max_timeout and self.get_task_result(task) is None:
      time.sleep(0.001)
    response = self.read_task_response(task)
    self.delete_task_response(task)
    return response

  def get_shared_model_response(self, analysis_value):
    return self.get_task_response(
      self.submit_task(
        self.task_message(analysis_value)
      )
    )

  def load(self):
    raise NotImplementedError("[SharedModel] Subclasses must define a `load` function to load their own model!")

  def respond(self, task_package):
    raise NotImplementedError("[SharedModel] Subclasses must define a `respond` function to process requests!")

  def similarity(self, vecA, vecB):
    raise NotImplementedError("[SharedModel] Subclasses must define a `similarity` function to compare values!")
