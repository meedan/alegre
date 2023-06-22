import unittest
import json
from opensearchpy import  OpenSearch
from flask import current_app as app

from app.test.base import BaseTestCase
from app.main.lib.text_similarity import get_vector_model_base_conditions, get_document_body

class TestTextSimilarity(BaseTestCase):
    test_model_key = 'indian-sbert'

    def setUp(self):
      super().setUp()
      es = OpenSearch(app.config['ELASTICSEARCH_URL'])
      es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], ignore=[400, 404])
      es.indices.create(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_mapping(
        body=json.load(open('./elasticsearch/alegre_similarity.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )

    def test_get_vector_model_base_conditions(self):
        # check that vector number not included in query about to be run
        query = get_vector_model_base_conditions({'content':'bananna'}, self.test_model_key, 0.5)
        assert query is not None
        # looking for nested query object
        # {'query': {'script_score': {'min_score': 1.5, 'query': {'bool': 
        #   {'must': [{'match': {'model': {'query': 'indian-sbert'}}}]}}, 
        #       'script': {'source': "cosineSimilarity(params.query_vector, 'vector_768') ...
        source_str = query['query']['script_score']['script']['source']
        assert source_str is not None
        # the 768 part of the key should no longer be there
        model_key = query['query']['script_score']['script']['params']['field']
        old_key_doesnt_match = 'vector_768' == model_key
        assert old_key_doesnt_match is False
        # the appropriate model key vector should be there
        key_matches = 'vector_'+self.test_model_key == model_key
        assert key_matches is True

    def test_get_document_body(self):
        test_content = {
                  'text': 'this is a test',
                  'models': [self.test_model_key],  # e.g. indian-sbert, not elasticsearch
                  'min_es_score': 0.1,
                  'content': 'let there be content',
                }
        body = get_document_body(body=test_content)
        # this should list the appropriate model
        assert body.get('model') is self.test_model_key
        assert body.get('model_'+self.test_model_key) is not None
        # this should include the appropriate model vector
        assert body.get('vector_'+self.test_model_key) is not None
        # this should NOT have the old vector_768 included
        assert body.get('vector_768') is None



        
if __name__ == '__main__':
    unittest.main()