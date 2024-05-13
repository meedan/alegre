import unittest
import json
from opensearchpy import helpers, OpenSearch, TransportError
from flask import current_app as app

from app.main import db
from app.test.base import BaseTestCase

class TestXLMRBertBaseNliStsbMeanTokensBlueprint(BaseTestCase):
    use_model_key = "xlm-r-bert-base-nli-stsb-mean-tokens"

    def test_xlm_r_bert_base_nli_stsb_mean_tokens_api(self):
        SharedModel.register_server("xlm_r_bert_base_nli_stsb_mean_tokens", "XlmRBertBaseNliStsbMeanTokens", {"model_name": "meedan/xlm-r-bert-base-nli-stsb-mean-tokens"})
        with self.client:
            response = self.client.post(
                '/model/vector',
                data=json.dumps({
                  "text": "this is a test",
                  "model": TestXLMRBertBaseNliStsbMeanTokensBlueprint.use_model_key,
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            vector = result['vector']

            response = self.client.post(
                '/model/similarity',
                data=json.dumps({
                  "vector1": vector,
                  "vector2": vector,
                  "model": TestXLMRBertBaseNliStsbMeanTokensBlueprint.use_model_key,
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            similarity = result['similarity']
            self.assertEqual(1.0, similarity)

            response = self.client.post(
                '/model/vector',
                data=json.dumps({
                  "text": "how to delete an invoice",
                  "model": TestXLMRBertBaseNliStsbMeanTokensBlueprint.use_model_key,
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            vector1 = result['vector']

            response = self.client.post(
                '/model/vector',
                data=json.dumps({
                  "text": "purge an invoice",
                  "model": TestXLMRBertBaseNliStsbMeanTokensBlueprint.use_model_key,
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            vector2 = result['vector']

            response = self.client.post(
                '/model/similarity',
                data=json.dumps({
                  "vector1": vector1,
                  "vector2": vector2,
                  "model": TestXLMRBertBaseNliStsbMeanTokensBlueprint.use_model_key,
                }),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            similarity = result['similarity']
            self.assertNotEqual(1.0, similarity)
            self.assertGreater(similarity, 0.7)
