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
        existing = db.session.query(ArticleModel).filter(ArticleModel.url==url).one()
        if existing:
            return existing.to_dict()
        else:
            article = ArticleModel.from_newspaper3k(self.get_article(url))
            return article.to_dict()