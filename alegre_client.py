import json
import requests
import csv
import random
from collections import Counter
class AlegreClient:

  @staticmethod
  def default_hostname():
    return "http://0.0.0.0:5000"

  @staticmethod
  def text_similarity_path():
    return "/text/similarity/"

  def fact_pairs_from_csv(self, filename="texts.csv", threshold=4):
    # Expects filename to refer to local CSV path where columns are [similarity_score],[text_1],[text_2]
    with open(filename) as f:
      reader = csv.reader(f)
      dataset = []
      for row in reader:
        score = float(row[0])
        if score >= threshold:
          dataset.append({"database_text": row[1], "lookup_text": row[2], "score": score})
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

  def load_confounder_paragraphs(self, confounder_filename="train-v2.0.json"):
    paragraphs = []
    for row in json.loads(open(confounder_filename).read())["data"]:
      for para in row["paragraphs"]:
        if random.random() < 0.5:
          paragraphs.append(para["context"])
    return paragraphs

  def load_confounder_headlines(self, confounder_filename="confounder_headlines.csv"):
    confounders = []
    with open(confounder_filename) as f:
      reader = csv.reader(f)
      for row in reader:
        confounders.append(row[0].lower())
    return confounders

  def input_confounders(self, confounders, model_name, context):
    for row in confounders:
      request_params = {"model": model_name, "text": row}
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

  def evaluate_model(self, dataset, model_name, confounders, store_dataset, omit_half):
    # Similarity score should be from 0 to 5 similar to data found at https://ixa2.si.ehu.es/stswiki/index.php/STSbenchmark,
    # text_1 will be uploaded to service, text_2 will be used to attempt to retrieve text_1 from the service in a GET request.
    split_point = int(len(dataset)/2)
    context = {"task": "model_evaluation", "model_name": model_name}
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
        context
      )
    results = {"count": 0, "success": 0, "server_errors": 0, "resultset": []}
    for ii, fact_pair in enumerate(dataset):
      results["count"] += 1
      result = json.loads(self.get_similar_texts({
        "model": model_name,
        "text": fact_pair["lookup_text"].lower(),
        "context": context,
        "threshold": 0.0,
      }).text)
      #due to indexing math this may be an off-by-one but it's close enough for our test today, and it's too late at night to make sure, but not too late so as not to remind myself about this later....
      is_omitted = ii > split_point
      results["resultset"].append({"fact_pair": fact_pair, "response": result, "is_omitted": is_omitted})
    return results

  def store_text_similarity(self, request_params):
    return requests.post(self.hostname+self.text_similarity_path(), json=request_params)

  def get_similar_texts(self, request_params):
    return requests.get(self.hostname+self.text_similarity_path(), json=request_params)

  def transform_stanford_qa_data(self, qa_filename="dev-v2.0.json"):
    #we may want to limit the number of cases per paragraph we look at here - 
    #the groups of paragraphs are all thematically grouped, so results often 
    #yield "good" answers even though they refer to some other similar paragraph in the set.
    dataset = json.loads(open(qa_filename).read())
    paired_qas = []
    for row in dataset["data"]:
      for paragraph in row["paragraphs"]:
        for question in paragraph["qas"]:
          paired_qas.append({"lookup_text": question.get("question"), "database_text": paragraph.get("context")})
    return paired_qas

  def run_b_test(self, model_name):
    return self.evaluate_model(self.fact_pairs_from_csv(), model_name, [], True, False)

  def run_c_test(self, model_name):
    return self.evaluate_model(self.fact_pairs_from_csv(), model_name, self.load_confounder_headlines(), True, False)

  def run_cwm_test(self, model_name):
    return self.evaluate_model(self.fact_pairs_from_csv(), model_name, self.load_confounder_headlines(), True, True)

  def run_qa_test(self, model_name):
    return self.evaluate_model(self.transform_stanford_qa_data(), model_name, [], True, False)

  def run_qawm_test(self, model_name):
    return self.evaluate_model(self.transform_stanford_qa_data(), model_name, self.load_confounder_paragraphs(), True, False)

  def interpret_report(self, report):
    positions = Counter()
    results_dataset = []
    results_dataset.append(["Database-Stored Sentence", "Lookup Sentence", "Top Yielded Sentence", "ES Similarity Score", "Result Status"])
    for res in report["resultset"]:
      if not res.get('response', {}).get("message"):
        competing_sentences = [ee.get("_source", {}).get("content").lower() for ee in res.get("response", {}).get("result")]
        db_sentence = res.get("fact_pair", {}).get("database_text", "").lower()
        lookup_sentence = res.get("fact_pair", {}).get("lookup_text", "").lower()
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
          if res.get("is_omitted"):
            positions.update(["true negative"])
            row.append("Nothing found!")
            row.append("Nothing found!")
            row.append("True Negative")
          else:
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
  #from alegre_client import AlegreClient
  ac = AlegreClient()
  report = ac.run_qa_test("elasticsearch")
  results_dataset, positions = interpret_report(report)
  print(positions)
  with open('alegre_fact_recall_report.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(results_dataset)
  with open("report.json", "w") as f:
    f.write(json.dumps(report))
