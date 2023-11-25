import json
import opensearchpy
from opensearchpy import OpenSearch
from app.main.lib.opensearch import get_all_documents_matching_context, update_or_create_document
from app.main.lib.error_log import ErrorLog
from opensearchpy.helpers import scan

from flask import request, current_app as app

from app.main.lib.language_analyzers import SUPPORTED_LANGUAGES
import cld3
def get_all_documents():
  es = OpenSearch(app.config['OPENSEARCH_URL'], timeout=30)
  try:
    docs = scan(es,
      size=10000,
      index=app.config['OPENSEARCH_SIMILARITY'],
    )
    for hit in docs:
      yield hit
  except opensearchpy.exceptions.NotFoundError as err:
    ErrorLog.notify(err)
    return []

def get_docs_to_transform(team_id, language=None):
    es = OpenSearch(app.config['OPENSEARCH_URL'], timeout=30)
    docs_to_transform = {}
    for doc in get_all_documents_matching_context({"team_id": team_id}):
        if not language:
            prediction = cld3.get_language(doc["_source"]["content"])
            if prediction and prediction.is_reliable and prediction.language in SUPPORTED_LANGUAGES:
                docs_to_transform[doc["_id"]] = prediction.language
        else:
            docs_to_transform[doc["_id"]] = language
    f = open(f"docs_to_transform_{team_id}.json", "w")
    f.write(json.dumps(docs_to_transform))
    f.close()
    return docs_to_transform

def get_cached_docs_to_transform(team_id, language=None):
    try:
        return json.loads(open(f"docs_to_transform_{team_id}.json").read())
    except:
        return get_docs_to_transform(team_id, language)

def store_updated_docs(docs_to_transform):
    es = OpenSearch(app.config['OPENSEARCH_URL'], timeout=30)
    for doc_id, language in docs_to_transform.items():
        try:
            already_done = es.get(index=app.config['OPENSEARCH_SIMILARITY']+"_"+language, id=doc_id)
        except opensearchpy.exceptions.NotFoundError:
            found_doc = es.get(index=app.config['OPENSEARCH_SIMILARITY'], id=doc_id)
            if found_doc:
                source = found_doc["_source"]
                keys_to_pop = [e for e in source.keys() if 'vector' in e or 'model_' in e]
                for k in keys_to_pop:
                    source.pop(k, None)
                fail_count = 0
                finished = False
                while not finished and fail_count < 5:
                    try:
                        update_or_create_document(source, doc_id, app.config['OPENSEARCH_SIMILARITY']+"_"+language)
                        finished = True
                    except opensearchpy.exceptions.ConnectionError:
                        fail_count += 1

def run(team_id, language=None):
    if language is not None and language not in SUPPORTED_LANGUAGES:
         raise Exception(f"Unsupported language: {language} is not a supported language.")
    docs_to_transform = get_cached_docs_to_transform(team_id, language)
    store_updated_docs(docs_to_transform)
