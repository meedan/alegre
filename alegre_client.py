import json
import requests
import csv
from collections import Counter
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

  def input_confounders(self, confounder_filename, model_name, context):
    with open(confounder_filename) as f:
      reader = csv.reader(f)
      for row in reader:
        request_params = {"model": model_name, "text": row[0].lower()}
        if context:
          request_params["context"] = context
        self.store_text_similarity(request_params)

  def get_for_text(text, model_name, context={}):
    if not context:
      context = {"task": "model_evaluation", "model_name": model_name}
    return json.loads(ac.get_similar_texts({
      "model": model_name,
      "text": text.lower(),
      "context": context,
      "threshold": 0.0,
    }).text)

  def evaluate_model(self, filename, model_name, confounder_filename=None, store_dataset=True, threshold=4):
    # Similarity score should be from 0 to 5 similar to data found at https://ixa2.si.ehu.es/stswiki/index.php/STSbenchmark,
    # text_1 will be uploaded to service, text_2 will be used to attempt to retrieve text_1 from the service in a GET request.
    dataset = self.fact_pairs_from_csv(filename, threshold)
    context = {"task": "model_evaluation", "model_name": model_name}
    if store_dataset:
      if confounder_filename:
        self.input_confounders(confounder_filename, model_name, context)
      self.input_cases(
        [f["fact_pair"][0].lower() for f in dataset],
        model_name,
        context
      )
    report = {"count": 0, "success": 0, "successes": [], "fails": [], "server_errors": 0, "resultset": []}
    for fact_pair in dataset:
      report["count"] += 1
      result = json.loads(self.get_similar_texts({
        "model": model_name,
        "text": fact_pair["fact_pair"][1].lower(),
        "context": context,
        "threshold": 0.0,
      }).text)
      report["resultset"].append({"fact_pair": fact_pair, "response": result})
      if result and result.get("result") and result["result"][0]["_source"]["content"].lower() == fact_pair["fact_pair"][0].lower():
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

def interpret_report(report):
  positions = Counter()
  results_dataset = []
  results_dataset.append(["Database-Stored Sentence", "Lookup Sentence", "Top Yielded Sentence", "ES Similarity Score", "Result Status"])
  for res in report["resultset"]:
    if not res.get('response', {}).get("message"):
      competing_sentences = [ee.get("_source", {}).get("content").lower() for ee in res.get("response", {}).get("result")]
      db_sentence = res.get("fact_pair").get("fact_pair")[0].lower()
      lookup_sentence = res.get("fact_pair").get("fact_pair")[1].lower()
      row = [db_sentence, lookup_sentence]
      if competing_sentences and db_sentence == competing_sentences[0]:
        positions.update([1])
        row.append(competing_sentences[0])
        row.append(res.get("response", {}).get("result")[0].get("_score"))
        row.append("Success")
      elif competing_sentences and db_sentence != competing_sentences[0] and db_sentence in competing_sentences:
        positions.update([competing_sentences.index(db_sentence)+1])
        row.append(competing_sentences[0])
        row.append(res.get("response", {}).get("result")[0].get("_score"))
        row.append("Partial Success")
      elif not competing_sentences:
        positions.update(["false negative"])
        row.append("Nothing found!")
        row.append("Nothing found!")
        row.append("False Negative")
      else:
        positions.update(["false positive"])
        row.append(competing_sentences[0])
        row.append(res.get("response", {}).get("result")[0].get("_score"))
        row.append("False Positive")
      results_dataset.append(row)
    else: 
      positions.update(["server error"])
  return results_dataset, positions

if __name__ == '__main__':
  # from alegre_client import AlegreClient
  ac = AlegreClient()
  report = ac.evaluate_model("texts.csv", "wordvec-glove-6B-50d", "confounder_headlines.csv", True)
  results_dataset, positions = interpret_report(report)
  print(positions)
  with open('alegre_fact_recall_report.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(results_dataset)
  with open("report.json", "w") as f:
    f.write(json.dumps(report))
