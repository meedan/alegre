import io
import urllib.request

from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from app.main import db

class ArticleModel(db.Model):
  """ Model for storing image related details """
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

  def to_dict(self):
    return {
      "title": self.title,
      "authors": self.authors,
      "publish_date": self.publish_date.strftime("%Y-%m-%d %H:%M:%S"),
      "text": self.text,
      "top_image": self.top_image,
      "movies": self.movies,
      "keywords": self.keywords,
      "summary": self.summary,
      "source_url": self.source_url,
      "tags": self.tags,
    }

  @staticmethod
  def from_newspaper3k(article):
    """Fetch an image from a URL and load it
      :param url: Image URL
      :returns: ImageModel object
    """
    return ArticleModel(
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
        text=article.text,
    )
