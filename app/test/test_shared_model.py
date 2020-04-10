import unittest
import json
import uuid
from flask import current_app as app
import redis

from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel, Task
class SharedModelStub(SharedModel):
  def respond(self, analysis_value):
      return analysis_value

  def task_package(self, analysis_value):
      return {
          "test_package": analysis_value
      }

class TestSharedModel(BaseTestCase):
  def setUp(self):
    r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
    r.flushall()

  def test_init(self):
    instance = SharedModelStub()
    self.assertEqual(instance.queue_name, "SharedModelStub")

  def test_get_task_timeout(self):
    instance = SharedModelStub()
    self.assertIsNone(instance.get_task(1))

  def test_get_task_non_timeout(self):
    instance = SharedModelStub()
    message = {"task_id": "blah", "task_type": "blah", "task_package": "blah"}
    instance.datastore.rpush("SharedModelStub", json.dumps(message))
    self.assertEqual(instance.get_task(1), Task(**message))

  def test_task_message(self):
    instance = SharedModelStub()
    message = instance.task_message("blah")._asdict()
    self.assertEqual(sorted(message.keys()), ['task_id', 'task_package', 'task_type'])
    self.assertEqual(message["task_package"], {'test_package': 'blah'})

  def test_send_response(self):
    instance = SharedModelStub()
    task = Task(**{"task_id": "blah", "task_type": "blah", "task_package": "blah"})
    instance.send_response(task, 1)
    self.assertEqual(json.loads(instance.datastore.get("blah").decode("utf-8")), {"response": 1})

  def test_get_tasks(self):
    instance = SharedModelStub()
    message = {"task_id": "blah", "task_type": "blah", "task_package": "blah"}
    instance.datastore.rpush("SharedModelStub", json.dumps(message))
    instance.datastore.rpush("SharedModelStub", json.dumps(message))
    self.assertEqual(instance.get_tasks(), [Task(**message), Task(**message)])

  def test_task_id(self):
    instance = SharedModelStub()
    task_id = instance.task_id()
    self.assertEqual(len(task_id), 36)
    self.assertEqual(task_id.count("-"), 4)

  def test_submit_task(self):
    instance = SharedModelStub()
    instance.submit_task(instance.task_message("blah"))
    self.assertEqual(instance.datastore.llen(instance.queue_name), 1)

  def test_submit_task(self):
    instance = SharedModelStub()
    self.assertIsInstance(instance.encode_task(instance.task_message("blah")), str)

  def test_push_task(self):
    instance = SharedModelStub()
    instance.push_task(instance.task_message("blah"))
    self.assertEqual(instance.datastore.llen(instance.queue_name), 1)

  def test_get_task_result(self):
    instance = SharedModelStub()
    task = instance.task_message("blah")
    instance.send_response(task, 1)
    self.assertEqual(json.loads(instance.get_task_result(task).decode("utf-8")), {'response': 1})

  def test_delete_task_response(self):
    instance = SharedModelStub()
    task = instance.task_message("blah")
    instance.send_response(task, 1)
    self.assertEqual(json.loads(instance.get_task_result(task).decode("utf-8")), {'response': 1})
    instance.delete_task_response(task)
    self.assertIsNone(instance.get_task_result(task))

  def read_task_response(self):
    instance = SharedModelStub()
    task = instance.task_message("blah")
    instance.send_response(task, 1)
    self.assertEqual(instance.read_task_response(task), 1)

  def get_task_response(self):
    instance = SharedModelStub()
    task = instance.task_message("blah")
    instance.send_response(task, 1)
    self.assertEqual(instance.get_task_response(task), 1)

  def get_shared_model_response(self):
    instance = SharedModelStub()
    self.assertEqual(instance.get_shared_model_response(1), 1)

if __name__ == '__main__':
    unittest.main()
