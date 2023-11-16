import unittest
import urllib.parse
import json
from opensearchpy import helpers, OpenSearch, TransportError
from flask import current_app as app
import numpy as np

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel
from unittest.mock import patch

class TestSimilarityBlueprint(BaseTestCase):
    maxDiff = None
    use_model_key = 'xlm-r-bert-base-nli-stsb-mean-tokens'
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

    def test_similarity_mapping(self):
      es = OpenSearch(app.config['ELASTICSEARCH_URL'])
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

            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            lookup = urllib.parse.urlencode({'text': 'this is a test'})
            response = self.client.get(
                '/text/similarity/?'+lookup,
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(4, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'something different'})
            response = self.client.get(
                '/text/similarity/?'+lookup,
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))
            lookup = urllib.parse.urlencode({'text': 'this is a test','context': json.dumps({'dbid': 12,'app': 'check'})})
            response = self.client.get(
                '/text/similarity/?'+lookup,
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))
            lookup = urllib.parse.urlencode({'text': 'this is a test','context': json.dumps({'dbid': [12, 13],'app': 'check'})})
            response = self.client.get(
                '/text/similarity/?'+lookup,
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))
            lookup = urllib.parse.urlencode({'text': 'this is a test','context': json.dumps({'dbid': [13],'app': 'check'})})
            response = self.client.get(
                '/text/similarity/?'+lookup,
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(0, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'this is a test','context': json.dumps({'dbid': [15],'app': 'check'})})
            response = self.client.get(
                '/text/similarity/?'+lookup,
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'this is a test','context': json.dumps({'dbid': 15,'app': 'check'})})
            response = self.client.get(
                '/text/similarity/?'+lookup,
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'Magnitude 4.5 quake strikes near Fort St. John', 'threshold': 0.7})
            response = self.client.get(
                '/text/similarity/?'+lookup,
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(2, len(result['result']))

    def test_elasticsearch_similarity_english_models_specified(self):
        with self.client:
            for term in json.load(open('./app/test/data/similarity.json')):
                term['text'] = term['content']
                term["models"] = ["elasticsearch"]
                del term['content']
                response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
                result = json.loads(response.data.decode())
                self.assertEqual(True, result['success'])

            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])

            lookup = urllib.parse.urlencode({'text': 'this is a test', 'min_es_score': 0.1, 'models': json.dumps(["elasticsearch"])})
            response = self.client.get(
                '/text/similarity/?'+lookup
            )
            result = json.loads(response.data.decode())
            self.assertEqual(4, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'this is a test', 'models': json.dumps(["elasticsearch"])})
            response = self.client.get(
                '/text/similarity/?'+lookup
            )
            result = json.loads(response.data.decode())
            self.assertEqual(4, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'something different', 'models': json.dumps(["elasticsearch"])})
            response = self.client.get(
                '/text/similarity/?'+lookup
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'this is a test', 'models': json.dumps(["elasticsearch"]), 'context': json.dumps({'dbid': 12,'app': 'check'})})
            response = self.client.get(
                '/text/similarity/?'+lookup
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'this is a test', 'models': json.dumps(["elasticsearch"]), 'context': json.dumps({'dbid': [12, 13],'app': 'check'})})
            response = self.client.get(
                '/text/similarity/?'+lookup
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'this is a test', 'models': json.dumps(["elasticsearch"]), 'context': json.dumps({'dbid': [13],'app': 'check'})})
            response = self.client.get(
                '/text/similarity/?'+lookup
            )
            result = json.loads(response.data.decode())
            self.assertEqual(0, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'this is a test', 'models': json.dumps(["elasticsearch"]), 'context': json.dumps({'dbid': [15],'app': 'check'})})
            response = self.client.get(
                '/text/similarity/?'+lookup,
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'this is a test', 'models': json.dumps(["elasticsearch"]), 'context': json.dumps({'dbid': 15,'app': 'check'})})
            response = self.client.get(
                '/text/similarity/?'+lookup
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'Magnitude 4.5 quake strikes near Fort St. John', 'threshold': 0.7, 'models': json.dumps(["elasticsearch"])})
            response = self.client.get('/text/similarity/?'+lookup)
            result = json.loads(response.data.decode())
            self.assertEqual(2, len(result['result']))

    def test_elasticsearch_update_text_listed_context(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': [54, 55] } }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            term2 = { 'text': 'how to slice a pizza', 'model': 'elasticsearch', 'context': { 'dbid': [54, 55] }, 'doc_id': doc["_id"]}
            post_response2 = self.client.post('/text/similarity/', data=json.dumps(term2), content_type='application/json')
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if doc["_id"] == e["_id"]][0]
            self.assertEqual(term2['text'], doc['_source']['content'])

    def test_elasticsearch_performs_correct_fuzzy_search(self):
        with self.client:
            term = { 'text': 'what even is a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 } }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            lookup = urllib.parse.urlencode({ 'text': 'what even is a bananna', 'model': 'elasticsearch', 'context': json.dumps({ 'dbid': 54 }) })
            post_response = self.client.get('/text/similarity/?'+lookup)
            post_response_fuzzy = self.client.get('/text/similarity/?fuzzy=true&'+lookup)
            self.assertGreater(json.loads(post_response_fuzzy.data.decode())["result"][0]["_score"], json.loads(post_response.data.decode())["result"][0]["_score"])
            post_response_fuzzy = self.client.get('/text/similarity/?fuzzy=false&'+lookup)
            self.assertEqual(json.loads(post_response_fuzzy.data.decode())["result"][0]["_score"], json.loads(post_response.data.decode())["result"][0]["_score"])

    def test_elasticsearch_update_text(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 } }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            term2 = { 'text': 'how to slice a pizza', 'model': 'elasticsearch', 'context': { 'dbid': 54 }, 'doc_id': doc["_id"]}
            post_response2 = self.client.post('/text/similarity/', data=json.dumps(term2), content_type='application/json')
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if doc["_id"] == e["_id"]][0]
            self.assertEqual(term2['text'], doc['_source']['content'])

    def test_elasticsearch_update_text_with_doc_id(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 }, 'doc_id': "123456" }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            term2 = { 'text': 'how to slice a pizza', 'model': 'elasticsearch', 'context': { 'dbid': 54 }, 'doc_id': "123456"}
            post_response2 = self.client.post('/text/similarity/', data=json.dumps(term2), content_type='application/json')
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if doc["_id"] == e["_id"]][0]
            self.assertEqual(term2['text'], doc['_source']['content'])

    def test_elasticsearch_delete_404(self):
        with self.client:
            delete_response = self.client.delete(
                '/text/similarity/',
                data=json.dumps({"doc_id": "abcdef", "text": "string"}),
                content_type='application/json'
            )
            self.assertEqual(404, delete_response.status_code)

    def test_elasticsearch_delete_200(self):
        with self.client:
            delete_response = self.client.delete(
                '/text/similarity/',
                data=json.dumps({"doc_id": "abcdef", "quiet": True, 'context': { 'dbid': 54 }}),
                content_type='application/json'
            )
            result = json.loads(delete_response.data.decode())
            self.assertEqual(200, delete_response.status_code)

    def test_elasticsearch_delete_text(self):
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 } }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            result = json.loads(post_response.data.decode())
            self.assertEqual(True, result['success'])
            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            delete_response = self.client.delete(
                '/text/similarity/',
                data=json.dumps({"doc_id": doc["_id"], 'context': { 'dbid': 54 }}),
                content_type='application/json'
            )
            result = json.loads(delete_response.data.decode())
            self.assertEqual('deleted', result['result'])
        with self.client:
            term = { 'doc_id': '123', 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 54 } }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            term = { 'doc_id': '123', 'text': 'how to slice a banana', 'model': 'elasticsearch', 'context': { 'dbid': 55 } }
            post_response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            result = json.loads(post_response.data.decode())
            self.assertEqual(True, result['success'])
            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            results = es.search(body={"query": {"match_all": {}}},index=app.config['ELASTICSEARCH_SIMILARITY'])
            doc = [e for e in results["hits"]["hits"] if e["_source"]['content'] == term['text']][0]
            delete_response = self.client.delete(
                '/text/similarity/',
                data=json.dumps({"doc_id": doc["_id"], 'context': { 'dbid': 54 }}),
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

            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            lookup = urllib.parse.urlencode({'text': 'नमस्ते मेरा नाम करीम है', 'language': 'en', 'threshold': 0.0})
            response = self.client.get(
                '/text/similarity/?'+lookup,
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(2, len(result['result']))

            lookup = urllib.parse.urlencode({'text': 'नमस्ते मेरा नाम करीम है', 'language': 'hi'})
            response = self.client.get(
                '/text/similarity/?'+lookup,
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

        es = OpenSearch(app.config['ELASTICSEARCH_URL'])
        es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
        lookup = urllib.parse.urlencode({'text': 'how to delete an invoice','model': TestSimilarityBlueprint.use_model_key,'context': json.dumps({'dbid': 54})})
        response = self.client.get(
            '/text/similarity/?'+lookup,
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

        lookup = urllib.parse.urlencode({'text': 'purge an invoice','model': TestSimilarityBlueprint.use_model_key,'threshold': 0.7,'context': json.dumps({'dbid': 54})})
        response = self.client.get(
            '/text/similarity/?'+lookup,
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        lookup = urllib.parse.urlencode({'text': 'purge an invoice','model': TestSimilarityBlueprint.use_model_key,'threshold': 0.7,'per_model_threshold': json.dumps({TestSimilarityBlueprint.use_model_key: 0.7}), 'context': json.dumps({'dbid': 54})})
        response = self.client.get(
            '/text/similarity/?'+lookup,
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

        lookup = urllib.parse.urlencode({'text': 'purge an invoice','model': TestSimilarityBlueprint.use_model_key,'threshold': 0.7})
        response = self.client.get(
            '/text/similarity/?'+lookup,
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

    def test_wrong_model_key(self):
        """
        Tests querying with a model key that doesn't match the one content was index with
        """
        with self.client:
            term = { 'text': 'how to slice a banana', 'model': TestSimilarityBlueprint.use_model_key, 'context': { 'dbid': 54 }}
            response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
            result = json.loads(response.data.decode())
            self.assertEqual(True, result['success'])

        es = OpenSearch(app.config['ELASTICSEARCH_URL'])
        es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])

        lookup = urllib.parse.urlencode({'text': 'how to slice a banana','model': TestSimilarityBlueprint.use_model_key,'context': json.dumps({'dbid': 54})})
        response = self.client.get(
            '/text/similarity/?'+lookup
        )
        result = json.loads(response.data.decode())
        self.assertEqual(0, len(result['result']))

    def test_model_similarity_without_text(self):
      with self.client:
        term = { 'text': 'how to delete an invoice', 'model': 'elasticsearch', 'context': { 'dbid': 54 }}
        response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(True, result['success'])

      lookup = urllib.parse.urlencode({'threshold': 0.7,'model': TestSimilarityBlueprint.use_model_key,'context': json.dumps({'dbid': 54})})
      response = self.client.get(
        '/text/similarity/?'+lookup,
        content_type='application/json'
      )
      result = json.loads(response.data.decode())
      self.assertEqual(0, len(result['result']))

    def test_model_similarity_with_vector(self):
      with self.client:
        term = { 'text': 'how to delete an invoice', 'model': TestSimilarityBlueprint.use_model_key, 'context': { 'dbid': 54 }}
        response = self.client.post('/text/similarity/', data=json.dumps(term), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(True, result['success'])

      es = OpenSearch(app.config['ELASTICSEARCH_URL'])
      es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])

      model = SharedModel.get_client(TestSimilarityBlueprint.use_model_key)
      vector = model.get_shared_model_response('how to delete an invoice')

      lookup = urllib.parse.urlencode({'text': 'how to delete an invoice', 'vector': json.dumps(vector),'model': TestSimilarityBlueprint.use_model_key,'context': json.dumps({'dbid': 54})})
      response = self.client.get(
          '/text/similarity/?'+lookup,
          content_type='application/json'
      )
      result = json.loads(response.data.decode())
      self.assertEqual(1, len(result['result']))


    def test_min_es_search(self):
        with self.client:
            data={
                'text':'min_es_score',
                'models':['elasticsearch'],
            }
            response = self.client.post('/text/similarity/', data=json.dumps(data), content_type='application/json')
            result = json.loads(response.data.decode())
            self.assertEqual(True, result['success'])

            es = OpenSearch(app.config['ELASTICSEARCH_URL'])
            es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
            
            lookup = urllib.parse.urlencode({'text':'min_es_score', 'models': json.dumps(["elasticsearch"])})
            response = self.client.get(
                '/text/similarity/?'+lookup
            )
            result = json.loads(response.data.decode())
            
            self.assertEqual(1, len(result['result']))
            data['min_es_score']=10+result['result'][0]['_score']

            lookup = urllib.parse.urlencode({'text':'min_es_score', 'models': json.dumps(["elasticsearch"])})
            response = self.client.get(
                '/text/similarity/?'+lookup
            )
            result = json.loads(response.data.decode())
            self.assertEqual(0, len(result['result']))

if __name__ == '__main__':
    unittest.main()
