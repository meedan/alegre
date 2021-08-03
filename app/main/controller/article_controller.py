from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from newspaper import Article

api = Namespace('article', description='article operations')
article_request = api.model('article_request', {
    'url': fields.String(required=True, description='article URL to be processed')
})

@api.route('/')
class ArticleResource(Resource):
    def get_article(self, url):
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()

    @api.response(200, 'article successfully queried.')
    @api.doc('Download and parse an article')
    @api.expect(article_request, validate=False)
    def get(self):
        if(request.args.get('url')):
            url=request.args.get('url')
        else:
            url=request.json['url']
        article = self.get_article(url)
        return {
            "title": article.title,
            "authors": article.authors,
            "publish_date": article.publish_date.strftime("%Y-%m-%d %H:%M:%S"),
            "text": article.text,
            "top_image": article.top_image,
            "movies": article.movies,
            "keywords": article.keywords,
            "summary": article.summary,
            "source_url": article.source_url,
            "tags": article.tags,
            "text": article.text,
        }