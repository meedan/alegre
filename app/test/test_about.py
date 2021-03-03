import unittest
import json
from elasticsearch import helpers, Elasticsearch, TransportError
from flask import current_app as app

from app.main import db
from app.test.base import BaseTestCase

class TestAboutBlueprint(BaseTestCase):
    def test_about_api(self):
        with self.client:
            response = self.client.get('/about/')
            result = json.loads(response.data.decode())
            self.assertTrue('elasticsearch' in result['text/similarity'])
            self.assertTrue('xlm-r-bert-base-nli-stsb-mean-tokens' in result['text/similarity'])
