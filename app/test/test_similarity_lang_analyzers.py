import unittest
import json
from opensearchpy import helpers, OpenSearch, TransportError
from flask import current_app as app
import numpy as np

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel
from unittest.mock import patch
from  app.main.lib import language_analyzers

class TestSimilarityBlueprint(BaseTestCase):
    maxDiff = None
    use_model_key = 'xlm-r-bert-base-nli-stsb-mean-tokens'
    test_model_key = 'indian-sbert'

    def setUp(self):
      super().setUp()
      es = OpenSearch(app.config['OPENSEARCH_URL'])
      es.indices.delete(index=app.config['OPENSEARCH_SIMILARITY'], ignore=[400, 404])
      es.indices.create(index=app.config['OPENSEARCH_SIMILARITY'])
      es.indices.put_mapping(
        body=json.load(open('./opensearch/alegre_similarity.json')),
        index=app.config['OPENSEARCH_SIMILARITY']
      )
      # also make sure all the language specific indices have been dropped and recreated
      # (this is slow and runs before each test)
      language_analyzers.init_indices()


    def test_all_analyzers(self):
        examples = [{ 'text': 'केले को कैसे काटें', 'language': 'hi'}, {'text': 'how to slice a banana', 'language': 'en'}, {'text': 'como rebanar un plátano', 'language': 'es'}, {'text': 'কিভাবে একটি কলা টুকরা করা হয়', 'language': 'bn'}]
        with self.client:
            for example in examples:
                response = self.client.post('/text/similarity/', data=json.dumps(example), content_type='application/json')
                result = json.loads(response.data.decode())
                self.assertEqual(True, result['success'])
                es = OpenSearch(app.config['OPENSEARCH_URL'])
                es.indices.refresh(index=app.config['OPENSEARCH_SIMILARITY']+"_"+example['language'])
                response = self.client.post(
                    '/text/similarity/search/',
                    data=json.dumps({
                      'text': example['text'],
                      'language': example['language'],
                      'threshold': 0.0
                    }),
                    content_type='application/json'
                )
                result = json.loads(response.data.decode())
                self.assertTrue(app.config['OPENSEARCH_SIMILARITY']+"_"+example['language'] in [e['index'] for e in result['result']])

    def test_auto_language_id(self):
        # language examples as input to language classifier
        examples = [{'text': 'केले को कैसे काटें', 'language': 'auto'}, # hi
                    {'text': 'how to slice a banana', 'language': 'auto'}, # en
                    {'text': 'como rebanar un plátano', 'language': 'auto'}, # es
                    {'text': 'কিভাবে একটি কলা টুকরা করা হয়', 'language': 'auto'}, # bn
                    {'text': 'yadda ake yanka ayaba', 'language': 'auto'}]  # ha  (but not supported)
        
        # expected language id classification for examples above
        expected_lang_ids = ['hi','en','es','bn', None]
        with self.client:
            for n in range(len(examples)):
                example = examples[n]
                expected_lang = expected_lang_ids[n]
                response = self.client.post('/text/similarity/', data=json.dumps(example), content_type='application/json')
                result = json.loads(response.data.decode()) # we are feeding in 'auto' expected correct id back
                self.assertEqual(True, result['success'])
                es = OpenSearch(app.config['OPENSEARCH_URL'])
                if expected_lang is None:
                    es.indices.refresh(index=app.config['OPENSEARCH_SIMILARITY'])
                else:
                    es.indices.refresh(index=app.config['OPENSEARCH_SIMILARITY']+"_"+expected_lang)
                response = self.client.post(
                    '/text/similarity/search/',
                    data=json.dumps({
                      'text': example['text'],
                      'language': expected_lang, # <- note correct lang id must be here
                      'threshold': 0.0
                    }),
                    content_type='application/json'
                )
                result = json.loads(response.data.decode())
                # indirectly checking classification by confirming which index was included in result
                index_alias = app.config['OPENSEARCH_SIMILARITY']
                if expected_lang is not None:
                    index_alias = app.config['OPENSEARCH_SIMILARITY']+"_"+expected_lang
                self.assertTrue(index_alias in [e['index'] for e in result['result']])

    def test_auto_language_query(self):
      # language examples as input to language classifier
      examples = [{'text': 'केले को कैसे काटें', 'language': 'hi'}, # hi
                  {'text': 'how to slice a banana', 'language': 'en'}, # en
                  {'text': 'como rebanar un plátano', 'language': 'es'}, # es
                  {'text': 'কিভাবে একটি কলা টুকরা করা হয়', 'language': 'bn'}, # bn
                  {'text': 'yadda ake yanka ayaba', 'language': 'ha'}]  # ha  (but not supported)
      
      # expected language id classification for examples above
      expected_lang_ids = ['hi','en','es','bn', None]
      with self.client:
          for n in range(len(examples)):
              example = examples[n]
              expected_lang = expected_lang_ids[n]
              response = self.client.post('/text/similarity/', data=json.dumps(example), content_type='application/json')
              result = json.loads(response.data.decode()) # we are feeding in 'auto' expected correct id back
              self.assertEqual(True, result['success'])
              es = OpenSearch(app.config['OPENSEARCH_URL'])
              if expected_lang is None:
                  es.indices.refresh(index=app.config['OPENSEARCH_SIMILARITY'])
              else:
                  es.indices.refresh(index=app.config['OPENSEARCH_SIMILARITY']+"_"+expected_lang)
              response = self.client.post(
                  '/text/similarity/search/',
                  data=json.dumps({
                    'text': example['text'],
                    'language': 'auto', # <- NOTE 'auto' should guess and find correct id
                    'threshold': 0.0
                  }),
                  content_type='application/json'
              )
              result = json.loads(response.data.decode())
              # indirectly checking classification by confirming which index was included in result
              index_alias = app.config['OPENSEARCH_SIMILARITY']
              if expected_lang is not None:
                  index_alias = app.config['OPENSEARCH_SIMILARITY']+"_"+expected_lang
              self.assertTrue(index_alias in [e['index'] for e in result['result']])
    

if __name__ == '__main__':
    unittest.main()