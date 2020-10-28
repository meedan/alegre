import requests
from sentence_transformers import SentenceTransformer
from flask import current_app as app

from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.similarity_measures import angular_similarity

class MultiSbert(SharedModel):
    def load(self):
        model_name = self.options.get('model_name', 'distiluse-base-multilingual-cased')
        if self.options.get("model_url"):
            try:
                self.model = SentenceTransformer(self.options.get("model_url"))
            except requests.exceptions.HTTPError as e:
                app.logger.info('Attempting to load model by model name in lieu of broken URL')
                self.model = SentenceTransformer(model_name)
        else:
            self.model = SentenceTransformer(model_name)

    def respond(self, doc):
      return self.vectorize(doc)

    def similarity(self, vecA, vecB):
        return angular_similarity(vecA, vecB)

    def vectorize(self, doc):
        """
        vectorize: Embed a text snippet in the vector space.
        """
        return self.model.encode([doc])[0].tolist()
