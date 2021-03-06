import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app
import numpy as np

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel

class TestSimilarityBlueprint(BaseTestCase):
    maxDiff = None
    use_model_key = 'xlm-r-bert-base-nli-stsb-mean-tokens'
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
      es.indices.close(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_settings(
        body=json.load(open('./elasticsearch/alegre_similarity_settings.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      es.indices.open(index=app.config['ELASTICSEARCH_SIMILARITY'])

    def test_similarity_mapping(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      mapping = es.indices.get_mapping(
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      self.assertDictEqual(
        json.load(open('./elasticsearch/alegre_similarity.json')),
        mapping[app.config['ELASTICSEARCH_SIMILARITY']]['mappings']
      )

    def test_elasticsearch_similarity_english(self):
        with self.client:
            for term in json.load(open('./app/test/data/similarity.json')):
                term['text'] = term['content']
                del term['content']
                response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
                result = json.loads(response.data.decode())
                self.assertEqual(True, result['success'])

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'this is a test'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(4, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'something different'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'this is a test',
                  'context': {
                    'dbid': 12,
                    'app': 'check'
                  }
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'this is a test',
                  'context': {
                    'dbid': [12, 13],
                    'app': 'check'
                  }
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'this is a test',
                  'context': {
                    'dbid': [13],
                    'app': 'check'
                  }
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(0, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'this is a test',
                  'context': {
                    'dbid': [15],
                    'app': 'check'
                  }
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'this is a test',
                  'context': {
                    'dbid': 15,
                    'app': 'check'
                  }
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'Magnitude 4.5 quake strikes near Fort St. John',
                  'threshold': 0.7
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(2, len(result['result']))

    def test_elasticsearch_update_text_listed_context(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': [54, 55] } }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            term2 = { 'text': 'how to slice a pizza', 'model': 'elasticsearch', 'context': { 'dbid': [54, 55] }, 'doc_id': doc["_id"]}
            post_response2 = self.client.post('/text/similarity/', data=json.dumps(term2), content_type='application/json')
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if doc["_id"] == e["_id"]][0]
            self.assertEqual(term2['text'], doc['_source']['content'])

    def test_elasticsearch_performs_correct_fuzzy_search(self):
        with self.client:
            term = { 'text': 'what even is a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 } }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            lookup = { 'text': 'what even is a bananna', 'model': 'elasticsearch', 'context': { 'dbid': 54 } }
            post_response = self.client.get('/text/similarity/', data=json.dumps(lookup), content_type='application/json')
            lookup["fuzzy"] = True
            post_response_fuzzy = self.client.get('/text/similarity/', data=json.dumps(lookup), content_type='application/json')
            self.assertGreater(json.loads(post_response_fuzzy.data.decode())["result"][0]["_score"], json.loads(post_response.data.decode())["result"][0]["_score"])
            lookup["fuzzy"] = False
            post_response_fuzzy = self.client.get('/text/similarity/', data=json.dumps(lookup), content_type='application/json')
            self.assertEqual(json.loads(post_response_fuzzy.data.decode())["result"][0]["_score"], json.loads(post_response.data.decode())["result"][0]["_score"])

    def test_elasticsearch_update_text(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 } }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            term2 = { 'text': 'how to slice a pizza', 'model': 'elasticsearch', 'context': { 'dbid': 54 }, 'doc_id': doc["_id"]}
            post_response2 = self.client.post('/text/similarity/', data=json.dumps(term2), content_type='application/json')
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if doc["_id"] == e["_id"]][0]
            self.assertEqual(term2['text'], doc['_source']['content'])

    def test_elasticsearch_update_text_with_doc_id(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 }, 'doc_id': "123456" }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            term2 = { 'text': 'how to slice a pizza', 'model': 'elasticsearch', 'context': { 'dbid': 54 }, 'doc_id': "123456"}
            post_response2 = self.client.post('/text/similarity/', data=json.dumps(term2), content_type='application/json')
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if doc["_id"] == e["_id"]][0]
            self.assertEqual(term2['text'], doc['_source']['content'])

    def test_elasticsearch_delete_404(self):
        with self.client:
            delete_response = self.client.delete(
                '/text/similarity/',
                data=json.dumps({"doc_id": "abcdef"}),
                content_type='application/json'
            )
            result = json.loads(delete_response.data.decode())
            self.assertEqual(404, delete_response.status_code)

    def test_elasticsearch_delete_text(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 } }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            result = json.loads(post_response.data.decode())
            self.assertEqual(True, result['success'])
            es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            delete_response = self.client.delete(
                '/text/similarity/',
                data=json.dumps({"doc_id": doc["_id"]}),
                content_type='application/json'
            )
            result = json.loads(delete_response.data.decode())
            self.assertEqual('deleted', result['result'])

    def test_elasticsearch_similarity_hindi(self):
        with self.client:
            for term in [
              { 'text': 'नमस्ते मेरा नाम करीम है' },
              { 'text': 'हॅलो माझे नाव करीम आहे' }
            ]:
              response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
              result = json.loads(response.data.decode())
              self.assertEqual(True, result['success'])

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'नमस्ते मेरा नाम करीम है',
                  'language': 'en'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(2, len(result['result']))

            response = self.client.get(
                '/text/similarity/',
                data=json.dumps({
                  'text': 'नमस्ते मेरा नाम करीम है',
                  'language': 'hi'
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

    def test_model_similarity(self):
        with self.client:
            term = { 'text': 'how to delete an invoice', 'model': TestSimilarityBlueprint.use_model_key, 'context': { 'dbid': 54 } }
            response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            result = json.loads(response.data.decode())
            self.assertEqual(True, result['success'])

        response = self.client.get(
            '/text/similarity/',
            data=json.dumps({
              'text': 'how to delete an invoice',
              'model': TestSimilarityBlueprint.use_model_key,
              'context': {
                'dbid': 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

        response = self.client.get(
            '/text/similarity/',
            data=json.dumps({
              'text': 'purge an invoice',
              'model': TestSimilarityBlueprint.use_model_key,
              'threshold': 0.7,
              'context': {
                'dbid': 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

        response = self.client.get(
            '/text/similarity/',
            data=json.dumps({
              'text': 'purge an invoice',
              'model': TestSimilarityBlueprint.use_model_key,
              'threshold': 0.7
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

    def test_wrong_model_key(self):	
        with self.client:	
            term = { 'text': 'how to slice a banana', 'model': TestSimilarityBlueprint.use_model_key, 'context': { 'dbid': 54 } }	
            response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')	
            result = json.loads(response.data.decode())	
            self.assertEqual(True, result['success'])	

        response = self.client.get(	
            '/text/similarity/',	
            data=json.dumps({	
              'text': 'how to slice a banana',	
              'model': TestSimilarityBlueprint.test_model_key,	
              'context': {	
                'dbid': 54	
              }	
            }),	
            content_type='application/json'	
        )	
        result = json.loads(response.data.decode())	
        self.assertEqual(0, len(result['result']))	

if __name__ == '__main__':
    unittest.main()
