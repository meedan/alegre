import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app
import numpy as np
import redis

from app.main import db
from app.test.base import BaseTestCase
from app.test.test_shared_model import SharedModelStub
from app.main.lib.shared_models.shared_model import SharedModel

class TestBulkUpdateSimilarityBlueprint(BaseTestCase):
    maxDiff = None
    use_model_key = 'multi-sbert'
    test_model_key = 'shared-model-test'

    def setUp(self):
      super().setUp()
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], ignore=[400, 404])
      es.indices.create(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_mapping(
        body=json.load(open('./elasticsearch/alegre_similarity.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      es.indices.close(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_settings(
        body=json.load(open('./elasticsearch/alegre_similarity_settings.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      es.indices.open(index=app.config['ELASTICSEARCH_SIMILARITY'])
      r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
      r.delete(SharedModelStub.model_key)
      r.delete('SharedModel:%s' % SharedModelStub.model_key)
      r.srem('SharedModel', SharedModelStub.model_key)

    def test_similarity_mapping(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      mapping = es.indices.get_mapping(
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      self.assertDictEqual(
        json.load(open('./elasticsearch/alegre_similarity.json')),
        mapping[app.config['ELASTICSEARCH_SIMILARITY']]['mappings']
      )

    def test_elasticsearch_insert_text_with_doc_id(self):
        with self.client:
          with patch('importlib.import_module', ) as mock_import:
            with patch('app.main.lib.shared_models.shared_model.SharedModel.bulk_run') as mock_bulk_run:
              ModuleStub = namedtuple('ModuleStub', 'SharedModelStub')
              mock_import.return_value = ModuleStub(SharedModelStub=SharedModelStub)
              SharedModel.start_server('SharedModelStub', SharedModelStub.model_key)
              term = { 'text': 'how to slice a banana', 'model': SharedModelStub.model_key, 'context': { 'dbid': 54 }, 'doc_id': "123456" }
              response = self.client.post('/text/bulk_update_similarity/', data=json.dumps({"documents": [term]}), content_type='application/json')
              result = json.loads(response.data.decode())
              self.assertTrue(result)
              self.assertTrue(result[0]['_id'], "123456")

if __name__ == '__main__':
    unittest.main()
