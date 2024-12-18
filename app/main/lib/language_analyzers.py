import json
from opensearchpy import OpenSearch
from flask import request, current_app as app
SUPPORTED_LANGUAGES = ["en", "pt", "es", "hi", "bn", "pt-br", "ar", "fr", "de", "cjk", "id"]
#via https://www.elastic.co/guide/en/opensearch/reference/current/analysis-lang-analyzer.html#bengali-analyzer
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
  },
  "ar": {
    "analysis": {
      "filter": {
        "arabic_stop": {
          "type":       "stop",
          "stopwords":  "_arabic_" 
        },
        "arabic_stemmer": {
          "type":       "stemmer",
          "language":   "arabic"
        }
      },
      "analyzer": {
        "rebuilt_ar": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "decimal_digit",
            "arabic_stop",
            "arabic_normalization",
            "arabic_stemmer"
          ]
        }
      }
    }
  },
  "fr": {
    "analysis": {
      "filter": {
        "french_elision": {
          "type":         "elision",
          "articles_case": True,
          "articles": [
              "l", "m", "t", "qu", "n", "s",
              "j", "d", "c", "jusqu", "quoiqu",
              "lorsqu", "puisqu"
            ]
        },
        "french_stop": {
          "type":       "stop",
          "stopwords":  "_french_" 
        },
        "french_stemmer": {
          "type":       "stemmer",
          "language":   "light_french"
        }
      },
      "analyzer": {
        "rebuilt_fr": {
          "tokenizer":  "standard",
          "filter": [
            "french_elision",
            "lowercase",
            "french_stop",
            "french_stemmer"
          ]
        }
      }
    }
  },
  "de": {
    "analysis": {
      "filter": {
        "german_stop": {
          "type":       "stop",
          "stopwords":  "_german_" 
        },
        "german_stemmer": {
          "type":       "stemmer",
          "language":   "light_german"
        }
      },
      "analyzer": {
        "rebuilt_de": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "german_stop",
            "german_normalization",
            "german_stemmer"
          ]
        }
      }
    }
  },
  "cjk": {
    "analysis": {
      "filter": {
        "english_stop": {
          "type":       "stop",
          "stopwords":  [
            "a", "and", "are", "as", "at", "be", "but", "by", "for",
            "if", "in", "into", "is", "it", "no", "not", "of", "on",
            "or", "s", "such", "t", "that", "the", "their", "then",
            "there", "these", "they", "this", "to", "was", "will",
            "with", "www"
          ]
        }
      },
      "analyzer": {
        "rebuilt_cjk": {
          "tokenizer":  "standard",
          "filter": [
            "cjk_width",
            "lowercase",
            "cjk_bigram",
            "english_stop"
          ]
        }
      }
    }
  },
  "id": {
    "analysis": {
      "filter": {
        "indonesian_stop": {
          "type":       "stop",
          "stopwords":  "_indonesian_" 
        },
        "indonesian_stemmer": {
          "type":       "stemmer",
          "language":   "indonesian"
        }
      },
      "analyzer": {
        "rebuilt_id": {
          "tokenizer":  "standard",
          "filter": [
            "lowercase",
            "indonesian_stop",
            "indonesian_stemmer"
          ]
        }
      }
    }
  }
}

def init_indices():
  es = OpenSearch(app.config['OPENSEARCH_URL'])
  indices = es.cat.indices(h='index', s='index').split()
  for lang in SUPPORTED_LANGUAGES:
    index_name = app.config['OPENSEARCH_SIMILARITY']+"_"+lang
    if index_name not in indices:
      es.indices.create(index=index_name)
    else:
      es.indices.delete(index=index_name)
      es.indices.create(index=index_name)
    es.indices.close(index=index_name)
    mapping = json.load(open('./opensearch/alegre_similarity_base.json'))
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
