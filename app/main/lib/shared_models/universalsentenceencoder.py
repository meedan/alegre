import sys, getopt
import math
import json
from collections import Counter
from datetime import datetime

import numpy as np
import scipy.spatial.distance
from redis.client import Redis
import tensorflow_hub as hub

from app.main.lib.shared_models.shared_model import SharedModel

class UniversalSentenceEncoder(SharedModel):
    def load_model(self, model_opts={}):
        model_path = model_opts.get('model_path', 'https://tfhub.dev/google/universal-sentence-encoder-large/5')
        self.model=hub.load(model_path)

    def respond(self, doc):
      return self.vectorize(doc).tolist()

    def vectorize(self, doc):
        """
        vectorize: Embedd a text snippet in the vector space.
        If doc is a list, the return value will be a matrix with each row corresponding to one element in the list.
        If doc is not a list, then the return value will be a vector.
        """
        if isinstance(doc,list):
            return self.model(doc).numpy()
        else:
            return self.model([doc]).numpy()[0]
