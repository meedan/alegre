import requests
from sentence_transformers import SentenceTransformer
from flask import current_app as app

from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.similarity_measures import angular_similarity

MAX_SBERT_LEN = app.config["MAX_SBERT_LEN"]

class XlmRBertBaseNliStsbMeanTokens(SharedModel):
    def load(self):
        model_name = self.options.get('model_name', 'meedan/xlm-r-bert-base-nli-stsb-mean-tokens')
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
        if len(doc)>MAX_SBERT_LEN:
            doc = doc[0:MAX_SBERT_LEN]
        return self.model.encode([doc])[0].tolist()
