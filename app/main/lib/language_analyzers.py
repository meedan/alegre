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
        "brazilian_keywords": {
          "type":       "keyword_marker",
          "keywords":   ["exemplo"] 
        },
        "brazilian_stemmer": {
          "type":       "stemmer",
          "language":   "brazilian"
        }
      },
      "analyzer": {
        "rebuilt_brazilian": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "brazilian_stop",
            "brazilian_keywords",
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
        "hindi_keywords": {
          "type":       "keyword_marker",
          "keywords":   ["उदाहरण"] 
        },
        "hindi_stemmer": {
          "type":       "stemmer",
          "language":   "hindi"
        }
      },
      "analyzer": {
        "rebuilt_hindi": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "decimal_digit",
            "hindi_keywords",
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
        "bengali_keywords": {
          "type":       "keyword_marker",
          "keywords":   ["উদাহরণ"] 
        },
        "bengali_stemmer": {
          "type":       "stemmer",
          "language":   "bengali"
        }
      },
      "analyzer": {
        "rebuilt_bengali": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "decimal_digit",
            "bengali_keywords",
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
    es.indices.close(index=index_name)
    es.indices.put_mapping(
      body=json.load(open('./elasticsearch/alegre_similarity_base.json')),
      # include_type_name=True,
      index=index_name
    )
    es.indices.put_settings(
      body=SETTINGS_BY_LANGUAGE[lang],
      # include_type_name=True,
      index=index_name
    )
    es.indices.open(index=index_name)    
