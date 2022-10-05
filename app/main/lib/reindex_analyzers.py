import json
import elasticsearch
from elasticsearch import Elasticsearch
from app.main.lib.elasticsearch import get_all_documents_matching_context, update_or_create_document
from elasticsearch.helpers import scan

from flask import request, current_app as app

from app.main.lib.language_analyzers import SUPPORTED_LANGUAGES
import cld3
def get_all_documents():
  es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=30)
  try:
    docs = scan(es,
      size=10000,
      index=app.config['ELASTICSEARCH_SIMILARITY'],
    )
    for hit in docs:
      yield hit
  except elasticsearch.exceptions.NotFoundError as err:
    app.extensions['pybrake'].notify(err)
    return []

def get_docs_to_transform(team_id, language=None):
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=30)
    docs_to_transform = {}
    for doc in get_all_documents_matching_context({"team_id": team_id}):
        if not language:
            prediction = cld3.get_language(doc["_source"]["content"])
            if prediction and prediction.is_reliable and prediction.language in SUPPORTED_LANGUAGES:
                docs_to_transform[doc["_id"]] = prediction.language
        else:
            docs_to_transform[doc["_id"]] = language
    f = open("docs_to_transform.json", "w")
    f.write(json.dumps(docs_to_transform))
    f.close()
    return docs_to_transform

def get_cached_docs_to_transform(team_id, language=None):
    try:
        return json.loads(open("docs_to_transform.json").read())
    except:
        return get_docs_to_transform(team_id, language)

def store_updated_docs(docs_to_transform):
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=30)
    for doc_id, language in docs_to_transform.items():
        try:
            already_done = es.get(index=app.config['ELASTICSEARCH_SIMILARITY']+"_"+language, id=doc_id)
        except elasticsearch.exceptions.NotFoundError:
            found_doc = es.get(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc_id)
            if found_doc:
                source = found_doc["_source"]
                keys_to_pop = [e for e in source.keys() if 'vector' in e or 'model_' in e]
                for k in keys_to_pop:
                    source.pop(k, None)
                update_or_create_document(source, doc_id, app.config['ELASTICSEARCH_SIMILARITY']+"_"+language)

def run(team_id, language=None):
    docs_to_transform = get_cached_docs_to_transform(team_id, language)
    store_updated_docs(docs_to_transform)