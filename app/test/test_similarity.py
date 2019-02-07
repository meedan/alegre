import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app
import numpy as np

from app.main import db, ds
from app.test.base import BaseTestCase

class TestSimilaryBlueprint(BaseTestCase):
    maxDiff = None

    def setUp(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.create(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.close(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_settings(
        body=json.load(open('./elasticsearch/alegre_similarity_settings.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      es.indices.open(index=app.config['ELASTICSEARCH_SIMILARITY'])
      es.indices.put_mapping(
        doc_type='_doc',
        body=json.load(open('./elasticsearch/alegre_similarity.json')),
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )

    def test_similarity_mapping(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      mapping = es.indices.get_mapping(
        doc_type='_doc',
        index=app.config['ELASTICSEARCH_SIMILARITY']
      )
      self.assertDictEqual(
        json.load(open('./elasticsearch/alegre_similarity.json')),
        mapping[app.config['ELASTICSEARCH_SIMILARITY']]['mappings']['_doc']
      )

    def test_similarity_api(self):
        with self.client:
            for term in json.load(open('./app/test/data/similarity.json')):
                del term['_type']
                term['text'] = term['content']
                del term['content']
                response = self.client.post('/similarity/', data=json.dumps(term), content_type='application/json')
                result = json.loads(response.data.decode())
                self.assertEqual(True, result['success'])

            response = self.client.post(
                '/similarity/query',
                data=json.dumps({
                  "text": "this is a test"
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(3, len(result['result']))

            response = self.client.post(
                '/similarity/query',
                data=json.dumps({
                  "text": "something different"
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            response = self.client.post(
                '/similarity/query',
                data=json.dumps({
                  "text": "this is a test",
                  "context": {
                    "dbid": 12
                  }
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(1, len(result['result']))

            response = self.client.post(
                '/similarity/query',
                data=json.dumps({
                  "text": "Magnitude 4.5 quake strikes near Fort St. John"
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(2, len(result['result']))

    @unittest.skipIf(ds == None, "model.txt file is missing")
    def test_wordvec_similarity_api(self):
        with self.client:
            term = { 'text': 'how to delete an invoice', 'type': 'wordvec', 'context': { 'dbid': 54 } }
            response = self.client.post('/similarity/', data=json.dumps(term), content_type='application/json')
            result = json.loads(response.data.decode())
            self.assertEqual(True, result['success'])

        response = self.client.post(
            '/similarity/query',
            data=json.dumps({
              "text": "how to delete an invoice",
              "context": {
                "dbid": 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        vector1 = np.asarray(result['result'][0]['_source']['vector'])
        vector2 = ds.vectorize('purge an invoice')
        similarity = ds.cosine_sim(vector1, vector2)
        self.assertGreater(similarity, 0.7)

        response = self.client.post(
            '/similarity/query',
            data=json.dumps({
              "text": "purge an invoice",
              "type": "wordvec",
              "context": {
                "dbid": 54
              }
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

        response = self.client.post(
            '/similarity/query',
            data=json.dumps({
              "text": "purge an invoice",
              "type": "wordvec",
              "threshold": 0.7
            }),
            content_type='application/json'
        )
        result = json.loads(response.data.decode())
        self.assertEqual(1, len(result['result']))
        similarity = result['result'][0]['_score']
        self.assertGreater(similarity, 0.7)

if __name__ == '__main__':
    unittest.main()
