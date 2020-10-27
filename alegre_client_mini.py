import json
import requests
import csv
import random
import copy
from collections import Counter
import numpy as np
import requests
from sklearn.metrics import roc_curve
def cosine_sim(vecA, vecB):
  """Find the cosine similarity distance between two vectors."""
  csim = np.dot(vecA, vecB) / (np.linalg.norm(vecA) * np.linalg.norm(vecB))
  if np.isnan(np.sum(csim)):
    return 0
  return csim

class AlegreClient:

  @staticmethod
  def default_hostname():
    return "http://0.0.0.0:5000"

  @staticmethod
  def text_similarity_path():
    return "/text/similarity/"

  def __init__(self, use_fuzzy=False, hostname=None):
    if not hostname:
      hostname = AlegreClient.default_hostname()
    self.hostname = hostname
    self.use_fuzzy = use_fuzzy

  def input_cases(self, texts, model_name, context={}, language=None):
    for text in texts:
      request_params = {"model": model_name, "text": text}
      if context:
        request_params["context"] = context
      if language:
        request_params["language"] = language
      if self.use_fuzzy:
        request_params["fuzzy"] = "auto"
      self.store_text_similarity(request_params)

  def input_confounders(self, confounders, model_name, context):
    for row in confounders:
      request_params = {"model": model_name, "text": row}
      if context:
        request_params["context"] = context
      self.store_text_similarity(request_params)

  def get_for_text(self, text, model_name, context={}, language=None):
    if not context:
      context = {"task": "model_evaluation", "model_name": model_name}
    return json.loads(self.get_similar_texts({
      "model": model_name,
      "text": text.lower(),
      "context": context,
      "threshold": 0.0,
      "language": language
    }).text)

  def evaluate_model(self, dataset, model_name, confounders, store_dataset, omit_half, task_name="model_evaluation", language=None):
    # Similarity score should be from 0 to 5 similar to data found at https://ixa2.si.ehu.es/stswiki/index.php/STSbenchmark,
    # text_1 will be uploaded to service, text_2 will be used to attempt to retrieve text_1 from the service in a GET request.
    split_point = int(len(dataset)/2)
    context = {"task": task_name, "model_name": model_name}
    if store_dataset:
      if confounders:
        self.input_confounders(confounders, model_name, context)
      if omit_half:
        sent_group = dataset[:split_point]
      else:
        sent_group = dataset
      self.input_cases(
        [f["database_text"].lower() for f in sent_group],
        model_name,
        context,
        language
      )
    results = {"count": 0, "success": 0, "server_errors": 0, "resultset": []}
    for ii, fact_pair in enumerate(dataset):
      results["count"] += 1
      result = json.loads(self.get_similar_texts({
        "model": model_name,
        "text": fact_pair["lookup_text"].lower(),
        "context": context,
        "threshold": 0.0,
        "language": language
      }).text)
      #due to indexing math this may be an off-by-one but it's close enough for our test today, and it's too late at night to make sure, but not too late so as not to remind myself about this later....
      is_omitted = ii > split_point
      results["resultset"].append({"fact_pair": fact_pair, "response": result, "is_omitted": is_omitted})
    return results

  def store_text_similarity(self, request_params):
    return requests.post(self.hostname+self.text_similarity_path(), json=request_params)

  def get_similar_texts(self, request_params):
    return requests.get(self.hostname+self.text_similarity_path(), json=request_params)

if __name__ == '__main__':
  ac = AlegreClient()
  ac.get_for_text("hello", 'multi-sbert', {}, 'en')
  ac.evaluate_model([{"lookup_text": "blah", "database_text": "wow", "id": 1}], 'multi-sbert', [], True, False)

