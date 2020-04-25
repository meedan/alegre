import sys, getopt
import math
import json
from collections import Counter
from datetime import datetime
import numpy as np
from redis.client import Redis
import tensorflow_hub as hub
import tensorflow_text

from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.similarity_measures import angular_similarity

class UniversalSentenceEncoder(SharedModel):
    def load(self):
        model_path = self.options.get('model_path')
        self.model = hub.load(model_path)

    def respond(self, doc):
      return self.vectorize(doc).tolist()

    def similarity(self, vecA, vecB):
        return angular_similarity(vecA, vecB)

    def vectorize(self, doc):
        """
        vectorize: Embed a text snippet in the vector space.
        """
        return self.model([doc]).numpy()[0]
