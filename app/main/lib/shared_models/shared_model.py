import time
import json
import uuid
from datetime import datetime
from collections import namedtuple

from redis import Redis

Task = namedtuple('Task', 'task_id task_type task_package')

class SharedModel(object):
  @classmethod
  def start_client(cls, datastore=Redis(), queue_name_override=None):
    return cls(datastore)

  @classmethod
  def start_local(cls, model_opts={}, datastore=Redis()):
    instance = cls(datastore)
    instance.load_model(model_opts)
    return instance

  @classmethod
  def start(cls, model_opts={}, datastore=Redis()):
    instance = cls(datastore)
    instance.load_model(model_opts)
    instance.bulk_run()

  def model_name(self):
    return self.__class__.__name__
    
  def __init__(self, datastore, queue_name_override=None):
    self.queue_name = self.model_name()
    if queue_name_override:
      self.queue_name = queue_name_override
    self.datastore = datastore

  def get_task(self, timeout=0):
    if self.datastore:
      response = self.datastore.blpop(self.queue_name, timeout)
      if response:
        return json.loads(response[1].decode("utf-8"))
    else:
      return None

  def send_response(self, task, response):
    self.datastore.set(task["task_id"], json.dumps({"response": response}))

  def run(self):
    while True:
      #could transform directly to opts instead of passing package along as a dict
      task = self.get_task()
      if task:
        self.send_response(
          task,
          self.respond(task["task_package"])
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
    print("Running Model...")
    while True:
      tasks = self.get_tasks()
      responses = self.respond([t["task_package"] for t in tasks])
      for i,response in enumerate(responses):
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
    return json.dumps(dict(task._asdict()))

  def push_task(self, task):
    return self.datastore.rpush(
      task.task_type,
      self.encode_task(task)
    )

  def get_task_result(self, task):
    return self.datastore.get(task.task_id)

  def delete_task_response(self, task):
    return self.datastore.delete(task.task_id)

  def read_task_response(self, task):
    return json.loads(
      self.get_task_result(task).decode("utf-8")
    )["response"]

  def get_task_response(self, task):
    while self.get_task_result(task) is None:
      time.sleep(0.001)
    response = self.read_task_response(task)
    self.delete_task_response(task)
    return response

  def get_shared_model_response(self, analysis_value):
    if self.datastore:
      return self.get_task_response(
        self.submit_task(
          self.task_message(analysis_value)
        )
      )
    else:
      return self.respond(analysis_value)

  def respond(self, task_package):
    raise NotImplementedError("SharedModel subclasses must define a `respond` function for accessing answers!")
