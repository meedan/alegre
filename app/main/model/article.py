import io
import urllib.request

from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from newspaper.cleaners import DocumentCleaner
from urllib.parse import urlparse

from app.main import db

def uri_validator(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except:
        return False

class ArticleModel(db.Model):
  """ Model for storing article related details """
  __tablename__ = 'articles'

  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(500, convert_unicode=True), nullable=False)
  authors = db.Column(ARRAY(db.String(255, convert_unicode=True)), nullable=True)
  publish_date = db.Column(db.DateTime, nullable=False)
  text = db.Column(db.Text, nullable=False)
  top_image = db.Column(db.String(500, convert_unicode=True), nullable=False)
  movies = db.Column(ARRAY(db.String(255, convert_unicode=True)), nullable=True)
  keywords = db.Column(ARRAY(db.String(255, convert_unicode=True)), nullable=True)
  summary = db.Column(db.Text, nullable=False)
  source_url = db.Column(db.String(255, convert_unicode=True), nullable=False)
  tags = db.Column(ARRAY(db.String(255, convert_unicode=True)), nullable=True)
  url = db.Column(db.String(255, convert_unicode=True), nullable=False, index=True)
  links = db.Column(ARRAY(db.String(255, convert_unicode=True)), nullable=True)

  def to_dict(self):
    date_strftime = None
    if self.publish_date:
        date_strftime = self.publish_date.strftime("%Y-%m-%d %H:%M:%S")
    return {
      "title": self.title,
      "authors": self.authors,
      "publish_date": date_strftime,
      "text": self.text,
      "top_image": self.top_image,
      "movies": self.movies,
      "keywords": self.keywords,
      "summary": self.summary,
      "source_url": self.source_url,
      "tags": self.tags,
      "links": self.links
    }

  @staticmethod
  def from_newspaper3k(article):
    """Fetch an article from a URL and load it
      :param article: Article object from Newspaper3k
      :returns: ArticleModel object
    """
    if article:
        document_cleaner = DocumentCleaner(article.config)
        article.doc = article.config.get_parser().fromstring(article.html)
        article.doc = document_cleaner.clean(article.doc)
        top_node = article.extractor.calculate_best_node(article.doc)
        links = []
        if top_node:
            links = [e.attrib.get("href") for e in article.extractor.parser.getElementsByTag(top_node, "a") if e.attrib.get("href")]
        full_links = []
        for link in links:
          if uri_validator(link):
            full_links.append(link)
          else:
            full_links.append(article.source_url+link)
        article_obj = ArticleModel(
            title=article.title,
            authors=article.authors,
            publish_date=article.publish_date,
            text=article.text,
            top_image=article.top_image,
            movies=article.movies,
            keywords=article.keywords,
            summary=article.summary,
            source_url=article.source_url,
            tags=article.tags,
            links=full_links
        )
        db.session.add(article_obj)
        article_obj.to_dict()
    else:
        return {"error": "Article Couldn't be parsed!"}