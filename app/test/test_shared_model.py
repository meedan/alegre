import unittest
import json
import uuid
from flask import current_app as app
from unittest.mock import patch
from collections import namedtuple

from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel, Task
from app.main.lib import redis_client

class SharedModelStub(SharedModel):
  model_key = 'shared-model-stub-key'

  def load(self):
    pass

  def respond(self, analysis_value):
    return [0.0]

  def similarity(self, valueA, valueB):
    return 0.0

class TestSharedModel(BaseTestCase):
  def setUp(self):
    super().setUp()
    r = redis_client.get_client()
    r.delete(SharedModelStub.model_key)
    r.delete('SharedModel:%s' % SharedModelStub.model_key)
    r.srem('SharedModel', SharedModelStub.model_key)

  def test_server_registration(self):
    with patch('importlib.import_module', ) as mock_import:
      with patch('app.main.lib.shared_models.shared_model.SharedModel.bulk_run') as mock_bulk_run:
        ModuleStub = namedtuple('ModuleStub', 'SharedModelStub')
        mock_import.return_value = ModuleStub(SharedModelStub=SharedModelStub)
        SharedModel.start_server('SharedModelStub', SharedModelStub.model_key)
        self.assertIsInstance(SharedModel.get_client(SharedModelStub.model_key), SharedModelClient)
        self.assertTrue(SharedModelStub.model_key in SharedModel.get_servers())

  def test_init(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    self.assertEqual(instance.queue_name, SharedModelStub.model_key)

  def test_get_task_timeout(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    self.assertIsNone(instance.get_task(1))

  def test_get_task_non_timeout(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    message = {"task_id": "blah", "task_type": "blah", "task_package": "blah"}
    instance.datastore.rpush(instance.queue_name, json.dumps(message))
    self.assertEqual(instance.get_task(1), Task(**message))

  def test_task_message(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    message = instance.task_message("blah")._asdict()
    self.assertEqual(sorted(message.keys()), ['task_id', 'task_package', 'task_type'])
    self.assertEqual(message["task_package"], {'test_package': 'blah'})

  def test_send_response(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    task = Task(**{"task_id": "blah", "task_type": "blah", "task_package": "blah"})
    instance.send_response(task, 1)
    self.assertEqual(json.loads(instance.datastore.get("blah").decode("utf-8")), {"response": 1})

  def test_get_tasks(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    message = {"task_id": "blah", "task_type": "blah", "task_package": "blah"}
    instance.datastore.rpush(instance.queue_name, json.dumps(message))
    instance.datastore.rpush(instance.queue_name, json.dumps(message))
    self.assertEqual(instance.get_tasks(), [Task(**message), Task(**message)])

  def test_task_id(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    task_id = instance.task_id()
    self.assertEqual(len(task_id), 36)
    self.assertEqual(task_id.count("-"), 4)

  def test_task_message(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    self.assertIsInstance(instance.task_message("blah"), Task)

  def test_submit_task(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    instance.submit_task(instance.task_message("blah"))
    self.assertEqual(instance.datastore.llen(instance.queue_name), 1)

  def test_encode_task(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    self.assertIsInstance(instance.encode_task(instance.task_message("blah")), str)

  def test_push_task(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    instance.push_task(instance.task_message("blah"))
    self.assertEqual(instance.datastore.llen(instance.queue_name), 1)

  def test_get_task_result(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    task = instance.task_message("blah")
    instance.send_response(task, 1)
    self.assertEqual(json.loads(instance.get_task_result(task).decode("utf-8")), {'response': 1})

  def test_delete_task_response(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    task = instance.task_message("blah")
    instance.send_response(task, 1)
    self.assertEqual(json.loads(instance.get_task_result(task).decode("utf-8")), {'response': 1})
    instance.delete_task_response(task)
    self.assertIsNone(instance.get_task_result(task))

  def read_task_response(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    task = instance.task_message("blah")
    instance.send_response(task, 1)
    self.assertEqual(instance.read_task_response(task), 1)

  def get_task_response(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    task = instance.task_message("blah")
    instance.send_response(task, 1)
    self.assertEqual(instance.get_task_response(task), 1)

  def get_shared_model_response(self):
    instance = SharedModelStub(SharedModelStub.model_key)
    self.assertEqual(instance.get_shared_model_response(1), 1)

if __name__ == '__main__':
    unittest.main()
