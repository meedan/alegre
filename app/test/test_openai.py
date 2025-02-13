import unittest
from unittest.mock import patch

from app.main.lib.text_similarity import get_document_body
from app.main.lib.openai import retrieve_openai_embeddings

class TestRetrieveOpenAIEmbeddings(unittest.TestCase):

    def test_openai_get_document_body(self):
        with patch('app.main.lib.text_similarity.retrieve_openai_embeddings') as mock_retrieve_openai_embeddings:

            # body = {
            #     "content": "sample content",
            #     "models": ["openai-text-embedding", "elasticsearch"],
            #     "context": {"key": "value"}
            # }
            test_content = {
                      'text': 'this is a test',
                      'models': ["openai-text-embedding-ada-002"],  # e.g. indian-sbert, not elasticsearch
                      'min_es_score': 0.1,
                      'content': 'let there be content',
                    }
            mock_retrieve_openai_embeddings.return_value = [0.1, 0.2, 0.3]

            result = get_document_body(test_content)

            mock_retrieve_openai_embeddings.assert_called_once_with(test_content['content'], "openai-text-embedding-ada-002")
            self.assertEqual({'text': 'this is a test', 'models': ['openai-text-embedding-ada-002'], 'min_es_score': 0.1, 'content': 'let there be content', 'model': 'openai-text-embedding-ada-002', 'vector_openai-text-embedding-ada-002': [0.1, 0.2, 0.3], 'model_openai-text-embedding-ada-002': 1}, result)


if __name__ == "__main__":
    unittest.main()
