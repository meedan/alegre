import sys
from flask import abort, request, current_app as app
from flask_restx import Resource, Namespace, fields
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
        try:
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()
            return article
        except:
            e = sys.exc_info()[0]
            app.logger.info(e)

    def respond(self, request):
        if(request.args.get('url')):
            url=request.args.get('url')
        else:
            url=request.json['url']
        existing_cases = db.session.query(ArticleModel).filter(ArticleModel.url==url).all()
        if existing_cases:
            return existing_cases[-1].to_dict()
        else:
            article = ArticleModel.from_newspaper3k(self.get_article(url))
            return article

    @api.response(200, 'article successfully queried.')
    @api.doc('Download and parse an article')
    @api.doc(params={'url': 'article URL to be processed'})
    def get(self):
        response = self.respond(request)
        if response.get("error"):
            abort(400, description=response.get("error"))
        else:
            return response

    @api.response(200, 'article successfully queried.')
    @api.doc('Download and parse an article')
    @api.expect(article_request, validate=False)
    def post(self):
        response = self.respond(request)
        if response.get("error"):
            abort(400, description=response.get("error"))
        else:
            return response
