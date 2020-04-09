import os.path
import numpy as np
from gensim.models.keyedvectors import KeyedVectors

from app.main.lib.shared_models.shared_model import SharedModel

class DocSim(SharedModel):
    @classmethod
    def start(cls, model_path='./data/model.txt', stopwords_path='./data/stopwords-en.txt', redis_server=None, queue_name_override=None):
        if os.path.isfile(model_path):
            model = KeyedVectors.load_word2vec_format(model_path)
            with open(stopwords_path, 'r') as fh:
                stopwords = fh.read().split(',')
            ds = DocSim(model, stopwords=stopwords, redis_server=redis_server, queue_name_override=queue_name_override)
            if ds.datastore:
                ds.bulk_run()
            else:
                return ds

    def __init__(self, w2v_model, stopwords=[], redis_server=None, queue_name_override=None):
        self.w2v_model = w2v_model
        self.stopwords = stopwords
        super().__init__(redis_server, queue_name_override)

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

    def cosine_sim(self, vecA, vecB):
        """Find the cosine similarity distance between two vectors."""
        csim = np.dot(vecA, vecB) / (np.linalg.norm(vecA) * np.linalg.norm(vecB))
        if np.isnan(np.sum(csim)):
            return 0
        return csim

    def calculate_similarity(self, source_doc, target_docs=[], threshold=0):
        """Calculates & returns similarity scores between given source document & all
        the target documents."""
        if isinstance(target_docs, str):
            target_docs = [target_docs]

        source_vec = self.vectorize(source_doc)
        results = []
        for doc in target_docs:
            target_vec = self.vectorize(doc)
            sim_score = self.cosine_sim(source_vec, target_vec)
            if sim_score > threshold:
                results.append({
                    'score' : sim_score,
                    'doc' : doc
                })
            # Sort results by score in desc order
            results.sort(key=lambda k : k['score'] , reverse=True)

        return results

    def respond(self, task_package):
        return self.vectorize(task_package["text"])

    def task_package(self, text):
        return {
            "text": text
        }
