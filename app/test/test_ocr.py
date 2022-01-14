# import unittest
# import json
# from google.cloud import vision

# from app.main import db
# from app.main.lib.google_client import get_credentialed_google_client
# from app.test.base import BaseTestCase

# class TestOcrBlueprint(BaseTestCase):
#     def test_ocr_api_successful(self):
#         with self.client:
#             response = self.client.get(
#                 '/image/ocr/',
#                 data=json.dumps({
#                   'url': 'https://i.imgur.com/ewGClFQ.png',
#                 }),
#                 content_type='application/json'
#             )
#             result = json.loads(response.data.decode())

#             self.assertIn('Translate this sentence', result['text'])
#             self.assertIn('عندي وقت في الساعة العاشرة', result['text'])

#     def test_ocr_api_image_without_text(self):
#         with self.client:
#             response = self.client.get(
#                 '/image/ocr/',
#                 data=json.dumps({
#                   'url': 'https://i.imgur.com/LgnKoPh.png',
#                 }),
#                 content_type='application/json'
#             )
#             result = json.loads(response.data.decode())
#             self.assertIsNone(result)

# if __name__ == '__main__':
#     unittest.main()
