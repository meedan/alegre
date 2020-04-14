import json
import requests
import csv
class AlegreClient:
    
  @staticmethod
  def default_hostname():
    return "http://0.0.0.0:5000"
  
  @staticmethod
  def text_similarity_path():
    return "/text/similarity/"
  
  def fact_pairs_from_csv(self, filename, threshold):
    # Expects filename to refer to local CSV path where columns are [similarity_score],[text_1],[text_2]
    with open(filename) as f:
      reader = csv.reader(f)
      dataset = []
      for row in reader:
        score = float(row[0])
        if score >= threshold:
          dataset.append({"fact_pair": [row[1], row[2]], "score": score})
    return dataset
  
  def __init__(self, hostname=None):
    if not hostname:
      hostname = AlegreClient.default_hostname()
    self.hostname = hostname
  
  def input_cases(self, texts, model_name, context={}):
    for text in texts:
      request_params = {"model": model_name, "text": text}
      if context:
        request_params["context"] = context
      self.store_text_similarity(request_params)
  
  def evaluate_model(self, filename, model_name, store_dataset=True, threshold=4):
    # Similarity score should be from 0 to 5 similar to data found at https://ixa2.si.ehu.es/stswiki/index.php/STSbenchmark,
    # text_1 will be uploaded to service, text_2 will be used to attempt to retrieve text_1 from the service in a GET request.
    dataset = self.fact_pairs_from_csv(filename, threshold)
    context = {"task": "model_evaluation", "model_name": model_name}
    if store_dataset:
      self.input_cases(
        [f["fact_pair"][0] for f in dataset],
        model_name,
        context
      )
    report = {"count": 0, "success": 0, "successes": [], "fails": [], "server_errors": 0}
    for fact_pair in dataset:
      report["count"] += 1
      result = json.loads(self.get_similar_texts({
        "model": model_name,
        "text": fact_pair["fact_pair"][1],
        "context": context
      }).text)
      if result and result.get("result") and result["result"][0]["_source"]["content"] == fact_pair["fact_pair"][0]:
        report["success"] += 1
        report["successes"].append(fact_pair)
      elif result.get("message") == "Internal Server Error":
        report["server_errors"] += 1
      else:
        report["fails"].append(fact_pair)
    return report
  
  def store_text_similarity(self, request_params):
    return requests.post(self.hostname+self.text_similarity_path(), json=request_params)
  
  def get_similar_texts(self, request_params):
    return requests.get(self.hostname+self.text_similarity_path(), json=request_params)


#ac = AlegreClient()
#report = ac.evaluate_model("texts.csv", "wordvec-glove-6B-50d", False)
