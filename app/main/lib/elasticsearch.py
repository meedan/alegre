# Elasticsearch helpers
import elasticsearch
from elasticsearch import Elasticsearch

from elasticsearch.helpers import scan

from flask import request, current_app as app

from app.main.lib.language_analyzers import SUPPORTED_LANGUAGES
def get_all_documents_matching_context(context):
  matches, clause_count = generate_matches(context)
  es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=30)
  conditions = [{
      'nested': {
          'score_mode': 'none',
          'path': 'context',
          'query': {
              'bool': {
                  'must': matches
              }
          }
      }
  }]
  body = {
      'query': {
          'bool': {
              'must': conditions
          }
      }
  }
  try:
    docs = scan(es,
      size=10000,
      query=body,
      index=app.config['ELASTICSEARCH_SIMILARITY'],
    )
    for hit in docs:
      yield hit
  except elasticsearch.exceptions.NotFoundError as err:
    app.extensions['pybrake'].notify(err)
    return []

def generate_matches(context):
    matches = []
    clause_count = 0
    for key in context:
        if isinstance(context[key], list):
            clause_count += len(context[key])
            matches.append({
                'query_string': { 'query': str.join(" OR ", [f"context.{key}: {v}" for v in context[key]])}
            })
        else:
            clause_count += 1
            matches.append({
                'match': { 'context.' + key: context[key] }
            })
    return matches, clause_count

def truncate_query(query, clause_count):
    if query and query is not None:
        return str.join(" ", query.split(" ")[:(app.config['MAX_CLAUSE_COUNT']-clause_count)])
    else:
        return None

def merge_contexts(body, found_doc):
    if not body.get("contexts"):
        body["contexts"] = [body["context"]]
    for context in found_doc["_source"].get("contexts", []):
        if context not in body["contexts"]:
            body["contexts"].append(context)
    return body

def update_or_create_document(body, doc_id, index):
  es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=30)
  result = None
  if doc_id:
      try:
          found_doc = es.get(index=index, id=doc_id)
      except elasticsearch.exceptions.NotFoundError:
          found_doc = None
      if found_doc:
          result = es.update(
              id=doc_id,
              body={"doc": merge_contexts(body, found_doc)},
              index=index
          )
      else:
          result = es.index(
              id=doc_id,
              body=body,
              index=index
          )
  else:
      result = es.index(
          body=body,
          index=index
      )
  return result

def store_document(body, doc_id, language=None):
    indices = [app.config['ELASTICSEARCH_SIMILARITY']]
    if language and language in SUPPORTED_LANGUAGES:
      indices.append(app.config['ELASTICSEARCH_SIMILARITY']+"_"+language)
    results = []
    for index in indices:
      results.append(update_or_create_document(body, doc_id, index))
    result = results[0]
    success = False
    if result['result'] == 'created' or result['result'] == 'updated':
        success = True
    return {
        'success': success
    }

def delete_context_from_found_doc(context, found_doc, doc_id):
    found_doc["contexts"] = [row for row in found_doc.get("contexts", []) if context != row]
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
    result = es.update(
        id=doc_id,
        body={"doc": found_doc},
        index=app.config['ELASTICSEARCH_SIMILARITY']
    )
    return result

def delete_document(doc_id, context, quiet):
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
    try:
        found_doc = es.get(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc_id)
    except elasticsearch.exceptions.NotFoundError:
        found_doc = None
    try:
        if found_doc and context in found_doc.get("contexts", []) and len(found_doc.get("contexts", [])) > 1:
            return delete_context_from_found_doc(context, found_doc, doc_id)
        else:
            return es.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc_id)
    except:
        if quiet:
            return {
                'failed': f"Doc Not Found for id {doc_id}! No Deletion Occurred - quiet failure requested, so 200 code returned."
            }
        else:
            return False
