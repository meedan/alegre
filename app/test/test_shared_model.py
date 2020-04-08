import unittest
import json
import uuid
from flask import current_app as app
import redis

from app.test.base import BaseTestCase
from app.main.lib.shared_models import SharedModel
class SharedModelStub(SharedModel):
  def respond(self, analysis_value):
      return analysis_value

  def task_package(self, analysis_value):
      return {
          "test_package": analysis_value
      }

class TestSharedModel(TestCase):
  @classmethod
  def redis(cls):
    return redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])

  def setUp(self):
    r = TestSharedModel.redis()
    r.flushall()

  def tearDown(self):
    r = TestSharedModel.redis()
    r.flushall()

  def test_init(self):
    instance = SharedModelStub(None)
    self.assertIsNone(instance.datastore)
    self.assertEqual(instance.queue_name, "SharedModelStub")
    blah_named_instance = SharedModelStub(None, "blah")
    self.assertEqual(blah_named_instance.queue_name, "blah")

  def test_get_task_timeout_redis(self):
    throwaway_named_instance = SharedModelStub(TestSharedModel.redis(), str(uuid.uuid4()))
    self.assertIsNone(throwaway_named_instance.get_task(1))

  def test_get_task_non_timeout_redis(self):
    redis_instance = TestSharedModel.redis()
    instance = SharedModelStub(redis_instance)
    message = {"blah": 1}
    redis_instance.rpush("SharedModelStub", json.dumps(message))
    self.assertEqual(instance.get_task(1), message)

  def test_get_task_timeout_no_redis(self):
    throwaway_named_instance = SharedModelStub(None, str(uuid.uuid4()))
    self.assertIsNone(throwaway_named_instance.get_task(1))

  def test_get_task_non_timeout_no_redis(self):
    instance = SharedModelStub(None)
    self.assertIsNone(instance.get_task(1))

  def test_send_response(self):
    redis_instance = TestSharedModel.redis()
    instance = SharedModelStub(redis_instance)
    instance.send_response({"task_id": "blah"}, 1)
    self.assertEqual(json.loads(redis_instance.get("blah").decode("utf-8")), {"response": 1})

  def test_get_tasks(self):
    redis_instance = TestSharedModel.redis()
    instance = SharedModelStub(redis_instance)
    message = {"blah": 1}
    redis_instance.rpush("SharedModelStub", json.dumps(message))
    redis_instance.rpush("SharedModelStub", json.dumps(message))
    self.assertEqual(instance.get_tasks(), [message, message])

  def test_task_id(self):
    instance = SharedModelStub(None)
    task_id = instance.task_id()
    self.assertEqual(len(task_id), 36)
    self.assertEqual(task_id.count("-"), 4)
    
  def test_task_message(self):
    instance = SharedModelStub(None)
    message = dict(instance.task_message("blah")._asdict())
    self.assertEqual(sorted(message.keys()), ['task_id', 'task_package', 'task_type'])
    self.assertEqual(message["task_package"], {'test_package': 'blah'})

  def test_submit_task(self):
    throwaway_named_instance = SharedModelStub(TestSharedModel.redis(), str(uuid.uuid4()))
    throwaway_named_instance.submit_task(throwaway_named_instance.task_message("blah"))
    self.assertEqual(throwaway_named_instance.datastore.llen(throwaway_named_instance.queue_name), 1)
    
  def test_submit_task(self):
    throwaway_named_instance = SharedModelStub(None, str(uuid.uuid4()))
    self.assertIsInstance(throwaway_named_instance.encode_task(instance.task_message("blah")), str)

  def test_push_task(self):
    throwaway_named_instance = SharedModelStub(TestSharedModel.redis(), str(uuid.uuid4()))
    throwaway_named_instance.push_task(throwaway_named_instance.task_message("blah"))
    self.assertEqual(throwaway_named_instance.datastore.llen(throwaway_named_instance.queue_name), 1)

  def test_get_task_result(self):
    redis_instance = TestSharedModel.redis()
    instance = SharedModelStub(redis_instance)
    task = throwaway_named_instance.task_message("blah")
    instance.send_response({"task_id": task.task_id}, 1)
    self.assertEqual(json.loads(instance.get_task_result(task).decode("utf-8")), {'response': 1})

  def test_delete_task_response(self):
    redis_instance = TestSharedModel.redis()
    instance = SharedModelStub(redis_instance)
    task = throwaway_named_instance.task_message("blah")
    instance.send_response({"task_id": task.task_id}, 1)
    self.assertEqual(json.loads(instance.get_task_result(task).decode("utf-8")), {'response': 1})
    instance.delete_task_response(task)
    self.assertIsNone(instance.get_task_result(task))

  def read_task_response(self):
    redis_instance = TestSharedModel.redis()
    instance = SharedModelStub(redis_instance)
    task = throwaway_named_instance.task_message("blah")
    instance.send_response({"task_id": task.task_id}, 1)
    self.assertEqual(instance.read_task_response(task), 1)

  def get_task_response(self):
    redis_instance = TestSharedModel.redis()
    instance = SharedModelStub(redis_instance)
    task = throwaway_named_instance.task_message("blah")
    instance.send_response({"task_id": task.task_id}, 1)
    self.assertEqual(instance.get_task_response(task), 1)

  def get_shared_model_response(self):
    instance = SharedModelStub(None)
    self.assertEqual(instance.get_shared_model_response(1), 1)

if __name__ == '__main__':
    unittest.main()
