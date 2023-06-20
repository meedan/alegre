from flask import current_app as app
from opensearchpy import Opensearch
from app.main.lib.elasticsearch import generate_matches, truncate_query, store_document, delete_document
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.language_analyzers import SUPPORTED_LANGUAGES
#from app.main.lib.langid import Cld3LangidProvider as LangidProvider
from app.main.lib.langid import GoogleLangidProvider as LangidProvider
from app.main.lib.openai import retrieve_openai_embeddings, PREFIX_OPENAI
ELASTICSEARCH_DEFAULT_LIMIT = 10000
def delete_text(doc_id, context, quiet):
  return delete_document(doc_id, context, quiet)

def get_document_body(body):
  for model_key in body.pop("models", []):
    context = body.get("context", {})
    if context:
      body["contexts"] = [context]
    if model_key != 'elasticsearch':
      if model_key[:len(PREFIX_OPENAI)] == PREFIX_OPENAI:
          vector = retrieve_openai_embeddings(body['content'], model_key)
          if vector == None:
             continue
      else:
          model = SharedModel.get_client(model_key)
          vector = model.get_shared_model_response(body['content'])
      body['model'] = model_key
      body['vector_'+model_key] = vector
    # Model key must be outside of the if statement
    body['model_'+model_key] = 1
  return body

def add_text(body, doc_id, language=None):
  document = store_document(get_document_body(body), doc_id, language)
  if 'error' in document:
    return document, 500
  return document

def search_text(search_params):
  results = {"result": []}
  for model_key in search_params.pop("models", []):
    result = search_text_by_model(dict(**search_params, **{'model': model_key}))
    if 'error' in result:
      app.extensions['pybrake'].notify(Exception('Model search failed when using '+model_key))
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
  if 'per_model_threshold' in search_params and search_params['per_model_threshold'].get(model_key):
      threshold = search_params['per_model_threshold'].get(model_key)
  if threshold is None:
      threshold = 0.9
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
                  'minimum_should_match': str(int(round(float(threshold) * 100))) + '%'
              }
            }
        },
    ]
    if 'fuzzy' in search_params:
        if str(search_params['fuzzy']).lower() == 'true':
            conditions[0]['match']['content']['fuzziness'] = 'AUTO'
    return conditions

def get_vector_model_base_conditions(search_params, model_key, threshold):
  if "vector" in search_params:
    vector = search_params["vector"]
  elif model_key[:len(PREFIX_OPENAI)] == PREFIX_OPENAI:
    vector = retrieve_openai_embeddings(search_params['content'], model_key)
    if vector == None:
       return None
  else:
    model = SharedModel.get_client(model_key)
    vector = model.get_shared_model_response(search_params['content'])
  return {
      'query': {
          'script_score': {
              'min_score': float(threshold)+1,
              'query': {
                  'bool': {
                      'must': [
                          {
                              'match': {
                                  'model_'+str(model_key): {
                                    'query': "1",
                                  }
                              }
                          }
                      ]
                  }
              },
              'script': {
                  'source': "cosineSimilarity(params.query_vector, doc[params.field]) + 1.0",
                  'params': {
                      'field': "vector_"+str(model_key),
                      'query_vector': vector
                  }
              }
          }
      }
  }

def insert_model_into_response(hits, model_key):
    for hit in hits:
        if "_source" in hit:
            hit["_source"]["model"] = model_key
    return hits

def strip_vectors(results):
    for result in results:
        vector_keys = [key for key in result["_source"].keys() if key[:7] == "vector_"]
        for key in vector_keys:
            result["_source"].pop(key, None)
    return results

def restrict_results(results, search_params, model_key):
    out_results = []
    if search_params.get("min_es_score") and model_key == "elasticsearch":
        for result in results:
            if "_score" in result and search_params.get("min_es_score", 0) < result["_score"]:
                out_results.append(result)
        return out_results
    return results

def search_text_by_model(search_params):
    app.logger.info(
        f"[Alegre Similarity] search_text_by_model:search_params {search_params}")
    language = None
    if not search_params.get("content"):
        return {"result": []}
    model_key, threshold = get_model_and_threshold(search_params)
    app.logger.info(
        f"[Alegre Similarity] search_text_by_model:model_key {model_key}, threshold:{threshold}")
    es = OpenSearch(app.config['ELASTICSEARCH_URL'], timeout=30)
    conditions = []
    matches = []
    clause_count = 0
    search_indices = [app.config['ELASTICSEARCH_SIMILARITY']]
    if 'context' in search_params:
        matches, clause_count = generate_matches(search_params['context'])
    if clause_count >= app.config['MAX_CLAUSE_COUNT']:
        return {'error': "Too many clauses specified! Text search will fail if another clause is added. Current clause count: "+str(clause_count)}
    if model_key.lower() == 'elasticsearch':
        conditions = get_elasticsearch_base_conditions(search_params, clause_count, threshold)
        language = search_params.get("language")
        # 'auto' indicates we should try to guess the appropriate language
        if language == 'auto':
            text = search_params.get("content")
            language = LangidProvider.langid(text)['result']['language']
            if language not in SUPPORTED_LANGUAGES:
                app.logger.warning('Detected language in query text {} is not explicitly supported for indexing, defaulting to "none"'.format(language))
                language = None
        if language in SUPPORTED_LANGUAGES:
            search_indices.append(app.config['ELASTICSEARCH_SIMILARITY']+"_"+language)
        elif language:
            error_text = f"[Alegre Similarity] [Similarity type: text] Language parameter value of {language} for text similarity search asserted, but not in SUPPORTED_LANGUAGES"
            app.logger.info(error_text)
            raise Exception(error_text)
    else:
        conditions = get_vector_model_base_conditions(search_params, model_key, threshold)
        if conditions==None:
           return {'result': []}
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
    limit = search_params.get("limit")
    result = es.search(
        size=limit or ELASTICSEARCH_DEFAULT_LIMIT,
        body=get_body_from_conditions(conditions),
        index=search_indices
    )
    response = strip_vectors(
        restrict_results(
            insert_model_into_response(result['hits']['hits'], model_key),
            search_params,
            model_key
        )
    )
    return {
        'result': response
    }
