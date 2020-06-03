from laserembeddings import Laser

from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.similarity_measures import angular_similarity

class LaserSharedModel(SharedModel):
    def load(self):
        self.model = Laser()

    def respond(self, doc):
      return self.vectorize(doc).tolist()[0]

    def similarity(self, vecA, vecB):
        return angular_similarity(vecA, vecB)

    def vectorize(self, doc):
        """
        vectorize: Embed a text snippet in the vector space.
        """
        if isinstance(doc, list):
            return self.model.embed_sentences(doc, lang='en')
        else:
            return self.model.embed_sentences([doc], lang='en')
