import json
from elasticsearch import Elasticsearch
from flask import request, current_app as app
SUPPORTED_LANGUAGES = ["en", "pt", "es", "hi", "bn", "pt-br"]
#via https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-lang-analyzer.html#bengali-analyzer
SETTINGS_BY_LANGUAGE = {
  "en": {
    "analysis": {
      "filter": {
        "english_stop": {
          "type":       "stop",
          "stopwords":  "_english_" 
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
        "rebuilt_en": {
          "tokenizer":  "standard",
          "filter": [
            "english_possessive_stemmer",
            "lowercase",
            "english_stop",
            "english_stemmer",
            "asciifolding",
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
        "spanish_stemmer": {
          "type":       "stemmer",
          "language":   "light_spanish"
        }
      },
      "analyzer": {
        "rebuilt_es": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "spanish_stop",
            "spanish_stemmer",
            "asciifolding",
          ]
        }
      }
    }
  },
  "pt-br": {
    "analysis": {
      "filter": {
        "brazilian_stop": {
          "type":       "stop",
          "stopwords":  "_brazilian_" 
        },
        "brazilian_stemmer": {
          "type":       "stemmer",
          "language":   "brazilian"
        }
      },
      "analyzer": {
        "rebuilt_pt-br": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "brazilian_stop",
            "brazilian_stemmer",
            "asciifolding",
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
        "portuguese_stemmer": {
          "type":       "stemmer",
          "language":   "light_portuguese"
        }
      },
      "analyzer": {
        "rebuilt_pt": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "portuguese_stop",
            "portuguese_stemmer",
            "asciifolding",
          ]
        }
      }
    }
  },
  "hi": {
    "analysis": {
      "filter": {
        "hindi_stop": {
          "type":       "stop",
          "stopwords":  "_hindi_" 
        },
        "hindi_stemmer": {
          "type":       "stemmer",
          "language":   "hindi"
        }
      },
      "analyzer": {
        "rebuilt_hi": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "decimal_digit",
            "indic_normalization",
            "hindi_normalization",
            "hindi_stop",
            "hindi_stemmer",
            "asciifolding",
          ]
        }
      }
    }
  },
  "bn": {
    "analysis": {
      "filter": {
        "bengali_stop": {
          "type":       "stop",
          "stopwords":  "_bengali_" 
        },
        "bengali_stemmer": {
          "type":       "stemmer",
          "language":   "bengali"
        }
      },
      "analyzer": {
        "rebuilt_bn": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "decimal_digit",
            "indic_normalization",
            "bengali_normalization",
            "bengali_stop",
            "bengali_stemmer",
            "asciifolding",
          ]
        }
      }
    }
  }
}

def init_indices():
  es = Elasticsearch(app.config['ELASTICSEARCH_URL'])
  indices = es.cat.indices(h='index', s='index').split()
  for lang in SUPPORTED_LANGUAGES:
    index_name = app.config['ELASTICSEARCH_SIMILARITY']+"_"+lang
    if index_name not in indices:
      es.indices.create(index=index_name)
    else:
      es.indices.delete(index=index_name)
      es.indices.create(index=index_name)
    es.indices.close(index=index_name)
    mapping = json.load(open('./elasticsearch/alegre_similarity_base.json'))
    mapping["properties"]["content"]["analyzer"] = "rebuilt_"+lang
    es.indices.put_settings(
      body=SETTINGS_BY_LANGUAGE[lang],
      # include_type_name=True,
      index=index_name
    )
    es.indices.put_mapping(
      body=mapping,
      # include_type_name=True,
      index=index_name
    )
    es.indices.open(index=index_name)    
