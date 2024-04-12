import unittest
import json
import os

from flask import current_app as app
from unittest.mock import patch
from unittest import mock
from google.cloud import vision
# from newspaper import Article

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.image_classification import GoogleImageClassificationProvider
from app.main.model.article import uri_validator
from app.main.lib import redis

class TestArticleBlueprint(BaseTestCase):
    def setUp(self):
        super().setUp()
        r = redis.get_client()
        for key in r.scan_iter("image_classification:*"):
            r.delete(key)

    # def test_article_api_post_endpoint(self):
    #     with patch('app.main.controller.article_controller.ArticleResource.get_article', ) as mock_get_article:
    #         article = Article("blah.com")
    #         article.set_html(open('./app/test/data/article.html').read())
    #         article.parse()
    #         article.nlp()
    #         mock_get_article.return_value = article
    #         response = self.client.post('/article/',
    #             data=json.dumps(dict(
    #                 url='http://fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones/'
    #             )),
    #             content_type='application/json'
    #         )
    #         result = json.loads(response.data.decode())
    #         self.assertEqual('application/json', response.content_type)
    #         self.assertEqual(200, response.status_code)
    #         self.assertEqual(sorted(result.keys()), ['authors', 'keywords', 'links', 'movies', 'publish_date', 'source_url', 'summary', 'tags', 'text', 'title', 'top_image'])

    # def test_article_api_get_endpoint(self):
    #     with patch('app.main.controller.article_controller.ArticleResource.get_article', ) as mock_get_article:
    #         article = Article("blah.com")
    #         article.set_html(open('./app/test/data/article.html').read())
    #         article.parse()
    #         article.nlp()
    #         mock_get_article.return_value = article
    #         response = self.client.post(
    #             '/article/',
    #             data=json.dumps(dict(
    #                 url='http://fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones/'
    #             )),
    #             content_type='application/json'
    #         )
    #         result = json.loads(response.data.decode())
    #         self.assertEqual('application/json', response.content_type)
    #         self.assertEqual(200, response.status_code)
    #         self.assertEqual(sorted(result.keys()), ['authors', 'keywords', 'links', 'movies', 'publish_date', 'source_url', 'summary', 'tags', 'text', 'title', 'top_image'])

    def test_article_api_error_response(self):
        with patch('app.main.controller.article_controller.ArticleResource.respond', ) as mock_get_error_response:
            mock_get_error_response.return_value = {"error": "response error"}
            response = self.client.post(
                '/article/',
                data=json.dumps(dict(
                    url='http://fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones/'
                )),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(400, response.status_code)

    def test_article_api_post_error_response(self):
        with patch('app.main.controller.article_controller.ArticleResource.respond', ) as mock_get_error_response:
            mock_get_error_response.return_value = {"error": "response error"}
            response = self.client.post(
                '/article/',
                data=json.dumps(dict(
                    url='http://fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones/'
                )),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(400, response.status_code)

    def test_article_not_parsed_response(self):
        with patch('app.main.controller.article_controller.ArticleResource.get_article', ) as mock_get_error_response:
            mock_get_error_response.return_value = None
            response = self.client.post(
                '/article/',
                data=json.dumps(dict(
                    url='http://fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones/'
                )),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual(400, response.status_code)
            self.assertIn("Article Couldn't be parsed", result['message'])


    # def test_article_download_error(self):
    #     with patch('newspaper.Article.download' ) as mock_download:
    #         mock_download.return_value = Exception()
    #         response = self.client.post(
    #             '/article/',
    #             data=json.dumps(dict(
    #                 url='http://fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones/'
    #             )),
    #             content_type='application/json'
    #         )
    #         result = json.loads(response.data.decode())
    #         self.assertEqual(400, response.status_code)
    #
    def test_uri_validator(self):
        url='http://fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones/'
        result = uri_validator(url)
        self.assertEqual(True, result)
        url2='fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones/'
        result = uri_validator(url2)
        self.assertEqual(False, result)
        # test error handle
        result = uri_validator(123456789)
        self.assertEqual(False, result)
        
    # def test_article_responds_with_top_node_extracted_links(self):
    #     with patch('app.main.controller.article_controller.ArticleResource.get_article', ) as mock_get_article:
    #         article = Article("blah.com")
    #         article.set_html(open('./app/test/data/article_with_top_node_links.html').read())
    #         article.parse()
    #         article.nlp()
    #         mock_get_article.return_value = article
    #         response = self.client.post('/article/',
    #             data=json.dumps(dict(
    #                 url='https://g1.globo.com/mundo/noticia/2022/05/06/hotel-em-havana-explosao.ghtml'
    #             )),
    #             content_type='application/json'
    #         )
    #         result = json.loads(response.data.decode())
    #         self.assertGreater(len(result["links"]), 0)


if __name__ == '__main__':
    unittest.main()