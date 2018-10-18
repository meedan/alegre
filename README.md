alegre
------

A linguistic service to support multilingual apps.

# Usage
```
$ python -m venv .alegre
$ source .alegre/bin/activate
$ make all
```

Then visit http://localhost:5000/

# Use cases
- Query multiple langid engines, such as langid.py, Google cld3, Meedan langid, etc.
- Compare results of each engine and annotate results for correcteness
- Query multiple engines for entity recognition, topic extraction, such as spaCy, Gensim, etc.
- Retrain engines with additional samples or new datasets
- Target different models per client application
- Provide translation memory / multilingual glossary service
- Provide locale-specific functions from ICU / CLDR
- Query existing API capabilities including target language for each available function (langid, ner, etc.)
