import unittest
import json
from elasticsearch import  Elasticsearch
from flask import current_app as app

from app.test.base import BaseTestCase
from app.main.lib.text_similarity import get_vector_model_base_conditions

class TestTextSimilarity(BaseTestCase):
    test_model_key = 'indian-sbert'

    def setUp(self):
      super().setUp()
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
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
        assert 'vector_768' not in source_str
        # the appropriate model key vector should be there
        assert 'vector_'+self.test_model_key in source_str
        
if __name__ == '__main__':
    unittest.main()