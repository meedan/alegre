from flask import current_app as app
from elasticsearch import Elasticsearch
from app.main.lib.elasticsearch import language_to_analyzer, generate_matches, truncate_query, store_document, delete_document
from app.main.lib.shared_models.shared_model import SharedModel

def delete_text(doc_id, quiet):
  return delete_document(doc_id, quiet)

def get_document_body(body):
  for model_key in body.pop("models", []):
    body['model_'+model_key] = 1
    if model_key != 'elasticsearch':
      model = SharedModel.get_client(model_key)
      vector = model.get_shared_model_response(body['content'])
      body['vector_'+str(len(vector))] = vector
      body['vector_'+model_key] = vector
      body['model'] = model_key
   return body

def add_text(body, doc_id):
  documents = []
  for model_key in body.pop("models", []):
    document = {}
    document = store_document(get_document_body(body, model_key), doc_id)
    documents.append(document)
    if 'error' in document:
      return document, 500
  if len(documents) == 1:
    return documents[0]
  else:
    return dict(**documents[0], **{"count": len(documents)})

def search_text(search_params):
  results = {"result": []}
  for model_key in search_params.pop("models", []):
    result = search_text_by_model(dict(**search_params, **{'model': model_key}))
    if 'error' in result:
      return result, 500
    for search_result in result["result"]:
      results["result"].append(search_result)
  return results

def get_model_and_threshold(search_params):
  model_key = 'elasticsearch'
  threshold = 0.9
  if 'model' in search_params:
      model_key = search_params['model']
  if 'threshold' in search_params:
      threshold = search_params['threshold']
  return model_key, threshold

def get_body_from_conditions(conditions):
    body = None
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
    return body

def get_elasticsearch_base_conditions(search_params, clause_count, threshold):
    conditions = [
        {
            'match': {
              'content': {
                  'query': truncate_query(search_params['content'], clause_count),
                  'minimum_should_match': str(int(round(threshold * 100))) + '%'
              }
            }
        },
    ]
    if 'fuzzy' in search_params:
        if str(search_params['fuzzy']).lower() == 'true':
            conditions[0]['match']['content']['fuzziness'] = 'AUTO'
    # FIXME: `analyzer` and `minimum_should_match` don't play well together.
    if 'language' in search_params:
        conditions[0]['match']['content']['analyzer'] = language_to_analyzer(search_params['language'])
        del conditions[0]['match']['content']['minimum_should_match']
    return conditions

def get_vector_model_base_conditions(search_params, model_key, threshold):
  if "vector" in search_params:
    vector = search_params["vector"]
  else:
    model = SharedModel.get_client(model_key)
    vector = model.get_shared_model_response(search_params['content'])
  return {
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

def search_text_by_model(search_params):
    if not search_params.get("content"):
        return {"result": []}
    model_key, threshold = get_model_and_threshold(search_params)
    es = Elasticsearch(app.config['ELASTICSEARCH_URL'], timeout=30)
    conditions = []
    matches = []
    clause_count = 0
    if 'context' in search_params:
        matches, clause_count = generate_matches(search_params['context'])
    if clause_count >= app.config['MAX_CLAUSE_COUNT']:
        return {'error': "Too many clauses specified! Text search will fail if another clause is added. Current clause count: "+str(clause_count)}
    if model_key.lower() == 'elasticsearch':
        conditions = get_elasticsearch_base_conditions(search_params, clause_count, threshold)
    else:
        conditions = get_vector_model_base_conditions(search_params, model_key, threshold)
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
    result = es.search(
        size=10000,
        body=get_body_from_conditions(conditions),
        index=app.config['ELASTICSEARCH_SIMILARITY']
    )
    return {
        'result': result['hits']['hits']
    }
