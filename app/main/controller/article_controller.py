from flask import request, current_app as app
from flask_restplus import Resource, Namespace, fields
from newspaper import Article
from app.main import db
from app.main.model.article import ArticleModel

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
        return article

    @api.response(200, 'article successfully queried.')
    @api.doc('Download and parse an article')
    @api.expect(article_request, validate=False)
    def get(self):
        if(request.args.get('url')):
            url=request.args.get('url')
        else:
            url=request.json['url']
        existing_cases = db.session.query(ArticleModel).filter(ArticleModel.url==url).all()
        if existing_cases:
            return existing_cases[-1].to_dict()
        else:
            article = ArticleModel.from_newspaper3k(self.get_article(url))
            return article.to_dict()