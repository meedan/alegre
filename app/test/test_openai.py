import unittest
from unittest.mock import patch
from app.main.lib.text_similarity import get_document_body
from app.main.lib.openai import retrieve_openai_embeddings
from app.main.lib.openai import PREFIX_OPENAI

class TestRetrieveOpenAIEmbeddings(unittest.TestCase):
    def test_retrieve_openai_embeddings_calls_openai_api(self):
        with patch('openai.embeddings_utils.get_embedding') as mock_get_embedding, \
                patch('app.main.lib.openai.redis_client.get_client') as mock_redis_client:
            mock_redis = mock_redis_client.return_value
            mock_redis.get.return_value = None  # Ensure cache is empty

            test_content = {
                'text': 'this is a test',
                'models': ["openai-text-embedding-ada-002"],
                'content': 'let there be content',
            }

            mock_get_embedding.return_value = [0.1, 0.2, 0.3]
            result = retrieve_openai_embeddings(test_content['content'], test_content['models'][0])
            mock_get_embedding.assert_called_once_with(test_content['content'],
                                                       engine=test_content['models'][0][len(PREFIX_OPENAI):])
            self.assertEqual(result, [0.1, 0.2, 0.3])

    def test_retrieve_openai_embeddings_handles_api_error(self):
        with patch('openai.embeddings_utils.get_embedding') as mock_get_embedding, \
                patch('app.main.lib.openai.redis_client.get_client') as mock_redis_client:
            mock_redis = mock_redis_client.return_value
            mock_redis.get.return_value = None  # Ensure cache is empty

            test_content = {
                'text': 'this is a test',
                'models': ["openai-text-embedding-ada-002"],
                'content': 'let there be content',
            }

            mock_get_embedding.side_effect = Exception("API Error")
            result = retrieve_openai_embeddings(test_content['content'], test_content['models'][0])
            mock_get_embedding.assert_called_once()
            self.assertIsNone(result)

    def test_openai_get_document_body(self):
        with patch('app.main.lib.text_similarity.retrieve_openai_embeddings') as mock_retrieve_openai_embeddings:
            test_content = {
                      'text': 'this is a test',
                      'models': ["openai-text-embedding-ada-002"],
                      'min_es_score': 0.1,
                      'content': 'let there be content',
                    }
            mock_retrieve_openai_embeddings.return_value = [0.1, 0.2, 0.3]

            result = get_document_body(test_content)

            mock_retrieve_openai_embeddings.assert_called_once_with(test_content['content'], "openai-text-embedding-ada-002")
            self.assertEqual({'text': 'this is a test', 'models': ['openai-text-embedding-ada-002'], 'min_es_score': 0.1, 'content': 'let there be content', 'model': 'openai-text-embedding-ada-002', 'vector_openai-text-embedding-ada-002': [0.1, 0.2, 0.3], 'model_openai-text-embedding-ada-002': 1}, result)

if __name__ == "__main__":
    unittest.main()
