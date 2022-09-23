from elasticsearch import Elasticsearch
from flask import request, current_app as app
settings_by_language = {
  "en": {
    "analysis": {
      "filter": {
        "english_stop": {
          "type":       "stop",
          "stopwords":  "_english_" 
        },
        "english_keywords": {
          "type":       "keyword_marker",
          "keywords":   ["example"] 
        },
        "english_stemmer": {
          "type":       "stemmer",
          "language":   "english"
        },
        "english_possessive_stemmer": {
          "type":       "stemmer",
          "language":   "possessive_english"
        }
      },
      "analyzer": {
        "rebuilt_english": {
          "tokenizer":  "standard",
          "filter": [
            "english_possessive_stemmer",
            "lowercase",
            "english_stop",
            "english_keywords",
            "english_stemmer"
          ]
        }
      }
    }
  },
  "es": {
    "analysis": {
      "filter": {
        "spanish_stop": {
          "type":       "stop",
          "stopwords":  "_spanish_" 
        },
        "spanish_keywords": {
          "type":       "keyword_marker",
          "keywords":   ["ejemplo"] 
        },
        "spanish_stemmer": {
          "type":       "stemmer",
          "language":   "light_spanish"
        }
      },
      "analyzer": {
        "rebuilt_spanish": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "spanish_stop",
            "spanish_keywords",
            "spanish_stemmer"
          ]
        }
      }
    }
  },
  "pt": {
    "analysis": {
      "filter": {
        "portuguese_stop": {
          "type":       "stop",
          "stopwords":  "_portuguese_" 
        },
        "portuguese_keywords": {
          "type":       "keyword_marker",
          "keywords":   ["exemplo"] 
        },
        "portuguese_stemmer": {
          "type":       "stemmer",
          "language":   "light_portuguese"
        }
      },
      "analyzer": {
        "rebuilt_portuguese": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "portuguese_stop",
            "portuguese_keywords",
            "portuguese_stemmer"
          ]
        }
      }
    }
  }
}
es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
#for PT lang:
es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY']+"_pt", ignore=[400, 404])
es.indices.create(index=app.config['ELASTICSEARCH_SIMILARITY']+"_pt")
es.indices.close(index=app.config['ELASTICSEARCH_SIMILARITY']+"_pt")
es.indices.put_mapping(
  body={
    "properties": {
      "content": {
        "type": "text"
      },
      "context": {
        "type": "nested"
      },
    }
  },
  # include_type_name=True,
  index=app.config['ELASTICSEARCH_SIMILARITY']+"_pt"
)
es.indices.put_settings(
  body=settings_by_language['pt'],
  # include_type_name=True,
  index=app.config['ELASTICSEARCH_SIMILARITY']+"_pt"
)
es.indices.open(index=app.config['ELASTICSEARCH_SIMILARITY']+"_pt")
texts = open("pt_text.txt").read().split(".")
results = []
for text in texts:
  results.append(es.index(
    body={"content": text, "context": {"foo": "bar"}},
    index=app.config['ELASTICSEARCH_SIMILARITY']+"_pt"
  ))
  
es.verdad

result = es.search(
  size=100,
  body={ 
    "query": { 
      "match": { 
        "content": "vacina" 
      } 
    } 
  },
  index=app.config['ELASTICSEARCH_SIMILARITY']+"_pt"
)
>>> len([e for e in result["hits"]["hits"] if "vacina " in e["_source"]["content"]])
62
>>> len(result["hits"]["hits"])
81
