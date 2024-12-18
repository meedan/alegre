import unittest
import json
from opensearchpy import helpers, OpenSearch, TransportError
from flask import current_app as app

from app.main import db
from app.test.base import BaseTestCase

class TestAboutBlueprint(BaseTestCase):
    def test_about_api(self):
        with self.client:
            response = self.client.get('/about/')
            result = json.loads(response.data.decode())
            self.assertTrue('opensearch' in result['text/similarity'])
            self.assertTrue('xlm-r-bert-base-nli-stsb-mean-tokens' in result['text/similarity'])
