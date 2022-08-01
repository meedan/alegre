# Elasticsearch helpers
import elasticsearch
from elasticsearch import Elasticsearch

from elasticsearch.helpers import scan

from flask import request, current_app as app
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

def store_document(body, doc_id):
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
    if doc_id:
        try:
            found_doc = es.get(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc_id)
        except elasticsearch.exceptions.NotFoundError:
            found_doc = None
        if found_doc:
            result = es.update(
                id=doc_id,
                body={"doc": body},
                index=app.config['ELASTICSEARCH_SIMILARITY']
            )
        else:
            result = es.index(
                id=doc_id,
                body=body,
                index=app.config['ELASTICSEARCH_SIMILARITY']
            )
    else:
        result = es.index(
            body=body,
            index=app.config['ELASTICSEARCH_SIMILARITY']
        )
    # es.indices.refresh(index=app.config['ELASTICSEARCH_SIMILARITY'])
    success = False
    if result['result'] == 'created' or result['result'] == 'updated':
        success = True
    return {
        'success': success
    }

def delete_document(doc_id, quiet, context):
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
    try:
        return es.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], id=doc_id)
    except:
        if quiet:
            return {
                'failed': f"Doc Not Found for id {doc_id}! No Deletion Occurred - quiet failure requested, so 200 code returned."
            }
        else:
            return False

def language_to_analyzer(lang):
    analyzer_dict = {
        'ar': 'arabic',
        'hy': 'armenian',
        'eu': 'basque',
        'bn': 'bengali',
        'pt-br': 'brazilian', # TODO
        'bg': 'bulgarian',
        'ca': 'catalan',
        'cjk': 'cjk', # TODO
        'cs': 'czech',
        'da': 'danish',
        'nl': 'dutch',
        'en': 'english',
        'fi': 'finnish',
        'fr': 'french',
        'gl': 'galician',
        'de': 'german',
        'gr': 'greek',
        'hi': 'hindi',
        'hu': 'hungarian',
        'id': 'indonesian',
        'ga': 'irish',
        'it': 'italian',
        'lv': 'latvian',
        'lt': 'lithuanian',
        'no': 'norwegian',
        'fa': 'persian',
        'pt': 'portuguese',
        'ro': 'romanian',
        'ru': 'russian',
        'ku': 'sorani',
        'es': 'spanish',
        'sv': 'swedish',
        'tr': 'turkish',
        'th': 'thai'
    }
    return analyzer_dict.get(lang, 'standard')
