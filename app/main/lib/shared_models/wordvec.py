import os.path
import numpy as np
from gensim.models.keyedvectors import KeyedVectors

from app.main.lib.shared_models.shared_model import SharedModel

class WordVec(SharedModel):
    def load_model(self, opts={}):
        model_path = opts.get("model_path", './data/model.txt')
        stopwords_path = opts.get("stopwords_path", './data/stopwords-en.txt')
        if os.path.isfile(model_path):
            w2v_model = KeyedVectors.load_word2vec_format(model_path)
            with open(stopwords_path, 'r') as fh:
                stopwords = fh.read().split(',')
            self.w2v_model = w2v_model
            self.stopwords = stopwords

    def respond(self, doc):
        if isinstance(doc,list):
            return [e.tolist() for e in self.vectorize(doc)]
        else:
            return self.vectorize(doc).tolist()

    def vectorize(self, doc):
        """Identify the vector values for each word in the given document"""
        if isinstance(doc,list):
            return [self.vectorize_single_doc(d) for d in doc]
        else:
            return self.vectorize_single_doc(doc)

    def vectorize_single_doc(self, doc):
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
