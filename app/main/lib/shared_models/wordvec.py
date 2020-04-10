import os.path
import numpy as np
from gensim.models.keyedvectors import KeyedVectors

from app.main.lib.shared_models.shared_model import SharedModel

class WordVec(SharedModel):
    # SharedModel interface
    def load(self):
        model_path = './data/model.txt'
        self.w2v_model = KeyedVectors.load_word2vec_format(model_path)

        stopwords_path = './data/stopwords-en.txt'
        with open(stopwords_path, 'r') as fh:
            stopwords = fh.read().split(',')
        self.stopwords = stopwords

    def respond(self, task_package):
        # Convert to regular array because we'll JSON-encode it
        # To convert the array back to ndarray: np.array(a)
        # https://stackoverflow.com/a/32850511/209184
        return self.vectorize(task_package["text"]).tolist()

    def task_package(self, text):
        return {
            "text": text
        }

    # WordVec implementation
    def vectorize(self, doc):
        """Identify the vector values for each word in the given document"""
        doc = doc.lower()
        words = [w for w in doc.split(" ") if w not in self.stopwords]
        word_vecs = []
        for word in words:
            try:
                vec = self.w2v_model[word]
                word_vecs.append(vec)
            except KeyError:
                # Ignore, if the word doesn't exist in the vocabulary
                pass

        # Assuming that document vector is the mean of all the word vectors
        # PS: There are other & better ways to do it.
        vector = np.mean(word_vecs, axis=0)
        return vector

    def similarity(self, vecA, vecB):
        """Find the cosine similarity distance between two vectors."""
        csim = np.dot(vecA, vecB) / (np.linalg.norm(vecA) * np.linalg.norm(vecB))
        if np.isnan(np.sum(csim)):
            return 0
        return csim
