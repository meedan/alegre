alegre
------

A linguistic service to support multilingual apps.

# Usage

Place your model file at `data/model.txt`, in Gensim format. Then:

```
docker-compose up
```

Then visit:
- http://localhost:5000 for the Alegre API
- http://localhost:5601 for the Kibana UI
- http://localhost:9200 for the Elasticsearch API

# Use cases
- Query multiple langid engines, such as langid.py, Google cld3, Meedan langid, etc.
- Compare results of each engine and annotate results for correcteness
- Query multiple engines for entity recognition, topic extraction, such as spaCy, Gensim, etc.
- Retrain engines with additional samples or new datasets
- Target different models per client application
- Provide translation memory / multilingual glossary service
- Provide locale-specific functions from ICU / CLDR
- Query existing API capabilities including target language for each available function (langid, ner, etc.)
- Find similar texts
