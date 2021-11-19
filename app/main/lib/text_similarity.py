from flask import current_app as app
from elasticsearch import Elasticsearch
from app.main.lib.elasticsearch import language_to_analyzer, generate_matches, truncate_query, store_document, delete_document
from app.main.lib.shared_models.shared_model import SharedModel
def delete_text(doc_id, quiet):
  return delete_document(doc_id, quiet)

def store_text(body, doc_id):
  return store_document(body, doc_id)

def search_text(search_params):
  model_key = 'elasticsearch'
  if 'model' in search_params:
      model_key = search_params['model']
  es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=30)
  conditions = []
  threshold = 0.9
  matches = []
  clause_count = 0
  if 'context' in search_params:
      matches, clause_count = generate_matches(search_params['context'])
  if 'threshold' in search_params:
      threshold = search_params['threshold']
  if clause_count >= app.config['MAX_CLAUSE_COUNT']:
      return {'error': "Too many clauses specified! Text search will fail if another clause is added. Current clause count: "+str(clause_count)}, 500
  if model_key.lower() == 'elasticsearch':
      conditions = [
          {
              'match': {
                'content': {
                    'query': truncate_query(search_params['text'], clause_count),
                    'minimum_should_match': str(int(round(threshold * 100))) + '%'
                }
              }
          },
      ]
      fuzzy = None
      if 'fuzzy' in search_params:
          if str(search_params['fuzzy']).lower() == 'true':
              conditions[0]['match']['content']['fuzziness'] = 'AUTO'
      # FIXME: `analyzer` and `minimum_should_match` don't play well together.
      if 'language' in search_params:
          conditions[0]['match']['content']['analyzer'] = language_to_analyzer(search_params['language'])
          del conditions[0]['match']['content']['minimum_should_match']

  else:
      if "vector" in search_params:
        vector = search_params["vector"]
      else:
        model = SharedModel.get_client(model_key)
        vector = model.get_shared_model_response(search_params['text'])
      conditions = {
          'query': {
              'script_score': {
                  'min_score': threshold+1,
                  'query': {
                      'bool': {
                          'must': [
                              {
                                  'match': {
                                      'model': {
                                        'query': model_key,
                                      }
                                  }
                              }
                          ]
                      }
                  },
                  'script': {
                      'source': "cosineSimilarity(params.query_vector, 'vector_"+str(len(vector))+"') + 1.0", 
                      'params': {
                          'query_vector': vector
                      }
                  }
              }
          }
      }
  if 'context' in search_params:
      context = {
          'nested': {
              'score_mode': 'none',
              'path': 'context',
              'query': {
                  'bool': {
                      'must': matches
                  }
              }
          }
      }
      if isinstance(conditions, list):
          conditions.append(context)
      else:
          conditions['query']['script_score']['query']['bool']['must'].append(context)
  if isinstance(conditions, list):
      body = {
          'query': {
              'bool': {
                  'must': conditions
              }
          }
      }
  else:
      body = conditions
  result = es.search(
      size=10000,
      body=body,
      index=app.config['ELASTICSEARCH_SIMILARITY']
  )
  return {
      'result': result['hits']['hits']
  }

  