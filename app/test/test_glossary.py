import unittest
import json
from elasticsearch import Elasticsearch, TransportError
from flask import current_app as app

from app.main import db
from app.test.base import BaseTestCase

class TestGlossaryBlueprint(BaseTestCase):
    maxDiff = None

    def test_glossary_mapping(self):
      es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
      mapping = es.indices.get_mapping(
        doc_type='_doc',
        index=app.config['ELASTICSEARCH_GLOSSARY']
      )
      self.assertDictEqual(
        mapping[app.config['ELASTICSEARCH_GLOSSARY']]['mappings']['_doc'],
        json.load(open('./elasticsearch/alegre_glossary.json'))
      )


if __name__ == '__main__':
    unittest.main()
