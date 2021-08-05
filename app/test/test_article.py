import unittest
import json
import os
import redis

from flask import current_app as app
from unittest.mock import patch
from google.cloud import vision
from newspaper import Article

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.image_classification import GoogleImageClassificationProvider

class TestArticleBlueprint(BaseTestCase):
    def setUp(self):
        super().setUp()
        r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
        for key in r.scan_iter("image_classification:*"):
            r.delete(key)

    def test_article_api(self):
        
        with patch('app.main.controller.article_controller.ArticleResource.get_article', ) as mock_get_article:
            article = Article("blah.com")
            article.set_html(open('./app/test/data/article.html').read())
            article.parse()
            article.nlp()
            mock_get_article.return_value = article
            response = self.client.get(
                '/article/',
                data=json.dumps(dict(
                    url='http://fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones/'
                )),
                content_type='application/json'
            )
            result = json.loads(response.data.decode())
            self.assertEqual('application/json', response.content_type)
            self.assertEqual(200, response.status_code)
            self.assertEqual(sorted(result.keys()), ['authors', 'keywords', 'links' 'movies', 'publish_date', 'source_url', 'summary', 'tags', 'text', 'title', 'top_image'])

if __name__ == '__main__':
    unittest.main()
