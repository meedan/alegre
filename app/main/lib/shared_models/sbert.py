from sentence_transformers import SentenceTransformer

from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.similarity_measures import angular_similarity

class Sbert(SharedModel):
    def load(self):
        self.model = SentenceTransformer('bert-base-nli-mean-tokens')

    def respond(self, doc):
      return self.vectorize(doc)[0].tolist()

    def similarity(self, vecA, vecB):
        return angular_similarity(vecA, vecB)

    def vectorize(self, doc):
        """
        vectorize: Embed a text snippet in the vector space.
        """
        if isinstance(doc, list):
            return self.model.encode(doc)
        else:
            return self.model.encode([doc])
        
