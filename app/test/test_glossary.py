import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app

from app.main import db
from app.test.base import BaseTestCase

class TestGlossaryBlueprint(BaseTestCase):
    maxDiff = None

    def setUp(self):
      super().setUp()
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      es.indices.delete(index=app.config['ELASTICSEARCH_GLOSSARY'], ignore=[400, 404])
      es.indices.create(index=app.config['ELASTICSEARCH_GLOSSARY'])
      es.indices.put_mapping(
        body=json.load(open('./elasticsearch/alegre_glossary.json')),
        index=app.config['ELASTICSEARCH_GLOSSARY']
      )

    def test_glossary_mapping(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      mapping = es.indices.get_mapping(
        index=app.config['ELASTICSEARCH_GLOSSARY']
      )
      print(mapping)
      self.assertDictEqual(
        json.load(open('./elasticsearch/alegre_glossary.json')),
        mapping[app.config['ELASTICSEARCH_GLOSSARY']]['mappings']
      )

    def test_glossary_queries(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      success, _ = helpers.bulk(es,
        json.load(open('./app/test/data/glossary.json')),
        index=app.config['ELASTICSEARCH_GLOSSARY']
      )
      self.assertTrue(success)
      es.indices.refresh(index=app.config['ELASTICSEARCH_GLOSSARY'])
      result = es.search(
        index=app.config['ELASTICSEARCH_GLOSSARY'],
        body={
          "query": {
            "simple_query_string": {
              "fields": [ "en" ],
              "query": "talking"
            }
          }
        }
      )
      self.assertEqual("Por que minha mãe conversa com a TV?", result['hits']['hits'][0]['_source']['pt'])
      result = es.search(
        index=app.config['ELASTICSEARCH_GLOSSARY'],
        body={
          "_source": ["pt"],
          "query": {
            "bool": {
              "must": [
                {
                  "match_phrase": { "en": "mothers talking" }
                },
                {
                  "nested": {
                    "path": "context",
                    "query": {
                      "bool": {
                        "must": [
                          {
                            "match": {
                              "context.user": "ccx"
                            }
                          }
                        ]
                      }
                    }
                  }
                }
              ],
              "filter": [
                { "exists": { "field": "pt" } }
              ]
            }
          }
        }
      )
      self.assertEqual("Por que minha mãe conversa com a TV?", result['hits']['hits'][0]['_source']['pt'])

    def test_glossary_api(self):
        with self.client:
            for term in json.load(open('./app/test/data/glossary.json')):
                response = self.client.post('/text/glossary/', data=json.dumps(term), content_type='application/json')
                result = json.loads(response.data.decode())
                self.assertEqual('created', result['result']['result'])

            response = self.client.get(
                '/text/glossary/',
                data=json.dumps({
                  "query": {
                    "simple_query_string": {
                      "fields": [ "en" ],
                      "query": "talking"
                    }
                  }
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual("Por que minha mãe conversa com a TV?", result['result']['hits']['hits'][0]['_source']['pt'])


if __name__ == '__main__':
    unittest.main()
