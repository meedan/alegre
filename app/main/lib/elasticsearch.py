# Elasticsearch helpers
import opensearchpy
from opensearchpy import OpenSearch

from opensearchpy.helpers import scan

from flask import current_app as app

from app.main.lib.language_analyzers import SUPPORTED_LANGUAGES
from app.main.lib.error_log import ErrorLog
#from app.main.lib.langid import Cld3LangidProvider as LangidProvider
from app.main.lib.langid import GoogleLangidProvider as LangidProvider

def get_all_documents_matching_context(context):
  matches, clause_count = generate_matches(context)
  es = OpenSearch(app.config['ELASTICSEARCH_URL'], timeout=30)
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
  except opensearchpy.exceptions.NotFoundError as err:
    ErrorLog.notify(err)
    return []

def generate_matches(context):
    matches = []
    clause_count = 0
    for key in context:
        if key not in ["project_media_id", "has_custom_id", "field"]:
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
  es = OpenSearch(app.config['ELASTICSEARCH_URL'], timeout=30)
  result = None
  if doc_id:
      try:
          found_doc = es.get(index=index, id=doc_id)
      except opensearchpy.exceptions.NotFoundError:
          found_doc = None
      if found_doc:
          body = {"doc": merge_contexts(body, found_doc)}
          app.logger.info(f"Sending OpenSearch update: {body}")
          result = es.update(
              id=doc_id,
              body=body,
              index=index,
              retry_on_conflict=3
          )
      else:
          app.logger.info(f"Sending OpenSearch store: {body}")
          result = es.index(
              id=doc_id,
              body=body,
              index=index
          )
  else:
      app.logger.info(f"Sending OpenSearch store without id: {body}")
      result = es.index(
          body=body,
          index=index
      )
  return result

def get_by_doc_id(doc_id):
    es = OpenSearch(app.config['ELASTICSEARCH_URL'])
    response = es.get(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc_id)
    return response['_source']

def store_document(body, doc_id, language=None):
    storable_doc = {}
    for k, v in body.items():
        if k not in ["per_model_threshold", "threshold", "model", "confirmed", "limit", "requires_callback"]:
            storable_doc[k] = v
    indices = [app.config['ELASTICSEARCH_SIMILARITY']]
    # 'auto' indicates we should try to guess the appropriate language
    if language == 'auto':
        text = storable_doc['content']
        language = LangidProvider.langid(text)['result']['language']
        if language not in SUPPORTED_LANGUAGES:
            app.logger.warning('Detected language {} is not supported'.format(language))
            language = None

    if (language is not None) and (language in SUPPORTED_LANGUAGES):
      # also cache in the language-specific index
      indices.append(app.config['ELASTICSEARCH_SIMILARITY']+"_"+language)
    
    results = []
    for index in indices:
      index_result = update_or_create_document(storable_doc, doc_id, index)
      results.append(index_result)
      if index_result['result'] not in ['created', 'updated', 'noop']:
          app.logger.warning('Problem adding document to ES index for language {0}: {1}'.format(language, index_result))
    result = results[0]
    success = False
    # Note: when we modify more than one index we are only checking the first result
    # should we report failure if any of them fail?
    if result['result'] == 'created' or result['result'] == 'updated':
        success = True
    return {
        'success': success
    }

def delete_context_from_found_doc(context, found_doc, doc_id):
    found_doc["contexts"] = [row for row in found_doc.get("contexts", []) if context != row]
    es = OpenSearch(app.config['ELASTICSEARCH_URL'])
    result = es.update(
        id=doc_id,
        body={"doc": found_doc},
        index=app.config['ELASTICSEARCH_SIMILARITY']
    )
    return result

def delete_document(doc_id, context, quiet):
    es = OpenSearch(app.config['ELASTICSEARCH_URL'])
    try:
        found_doc = es.get(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc_id)
    except opensearchpy.exceptions.NotFoundError:
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
