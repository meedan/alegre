# Alegre

A linguistic service by [Meedan](https://meedan.com).

## Installation

* Copy `config/config.yml.example` to `config/config.yml` and adjust the options
* Copy `config/database.yml.example` to `config/database.yml` and adjust the options
* Copy `config/initializers/secret_token.rb.example` to `config/initializers/secret_token.rb` and adjust the options
* Copy `config/initializers/errbit.rb.example` to `config/initializers/errbit.rb` and adjust the options
* Run `bundle install` to install Ruby dependencies
* Run `pip install -r requirements.txt` to install Python dependencies
* Run `docker pull elasticsearch:latest && docker run -d -p 9200:9200 elasticsearch` to install and start Elasticsearch
* Run `bundle exec rake db:migrate` to create database schema
* Run `bundle exec rake lapis:api_keys:create` to create API key - you will need it on the API web interface later!
* Run `bundle exec rake swagger:docs` to generate web-based documentation
* Run `cd doc && make` to generate full documentation
* Run `RAILS_ENV=test bundle exec rake db:migrate && bundle exec rake test` to run unit tests
* Run `rails s` and access the API at [http://localhost:3000/api](http://localhost:3000/api)

## Features

* Language identification
* Glossary
* Dictionary
* Machine Translation

## API

#### GET /api/languages/identification

Use this method in order to identify the language of a given text

**Parameters**

* `text`: Text to be classified _(required)_

**Response**

200: Text language
```json
{
  "type": "language",
  "data": [
    [
      "EN",
      1
    ],
    [
      "FR",
      0
    ],
    [
      "ES",
      0
    ],
    [
      "IT",
      0
    ],
    [
      "PT",
      0
    ],
    [
      "TR",
      0
    ],
    [
      "ID",
      0
    ],
    [
      "TL",
      0
    ],
    [
      "AZ",
      0
    ],
    [
      "RU",
      0
    ],
    [
      "KA",
      0
    ],
    [
      "HI",
      0
    ],
    [
      "AR",
      0
    ],
    [
      "FA",
      0
    ],
    [
      "ZH-CHS",
      0
    ],
    [
      "ZH-CHT",
      0
    ]
  ]
}
```

400: Parameter "text" is missing
```json
{
  "type": "error",
  "data": {
    "message": "Parameters missing",
    "code": 2
  }
}
```

401: Access denied
```json
{
  "type": "error",
  "data": {
    "message": "Unauthorized",
    "code": 1
  }
}
```


#### GET /api/glossary/terms

Use this method in order to get terms from glossary

**Parameters**

* `data`: JSON string that represents the input text _(required)_

**Response**

200: Terms from the glossary for the given input
```json
{
  "type": "term",
  "data": [
    {
      "_index": "glossary_mlg",
      "_type": "glossary",
      "_id": "e660012bdb8d50165a9c8ebfb1603c6b",
      "_score": 0.20786226,
      "_source": {
        "term": "Test",
        "lang": "en",
        "definition": "An experiment",
        "translations": [
          {
            "lang": "pt",
            "definition": "Um experimento",
            "term": "Teste"
          },
          {
            "lang": "es",
            "definition": "Un experimento",
            "term": "Teste"
          }
        ],
        "context": {
          "page_id": "foo",
          "data_source": "glossary"
        },
        "en": "Test"
      }
    }
  ]
}
```

400: Missing parameters
```json
{
  "type": "error",
  "data": {
    "message": "Parameters missing",
    "code": 2
  }
}
```

401: Access denied
```json
{
  "type": "error",
  "data": {
    "message": "Unauthorized",
    "code": 1
  }
}
```


#### POST /api/glossary/term

Use this method in order to add a new term to the glossary

**Parameters**

* `data`: JSON string that represents the term _(required)_
* `should_replace`: 0 or 1 telling whether an existing term should be replaced

**Response**

200: Term was added successfully
```json
{
  "type": "success",
  "data": true
}
```

400: Missing parameters
```json
{
  "type": "error",
  "data": {
    "message": "Parameters missing",
    "code": 2
  }
}
```

401: Access denied
```json
{
  "type": "error",
  "data": {
    "message": "Unauthorized",
    "code": 1
  }
}
```


#### DELETE /api/glossary/delete

Use this method in order to delete a term from the glossary

**Parameters**

* `id`: The term ID as assigned by ElasticSearch _(required)_

**Response**

200: Terms from the glossary for the given input
```json
{
  "type": "delete",
  "data": true
}
```

400: Missing parameters
```json
{
  "type": "error",
  "data": {
    "message": "Parameters missing",
    "code": 2
  }
}
```

401: Access denied
```json
{
  "type": "error",
  "data": {
    "message": "Unauthorized",
    "code": 1
  }
}
```


#### GET /api/dictionary/terms

Get dictionary terms (from Babelfy for the first time, then from ElasticSearch) for a text in a certain language

**Parameters**

* `text`: Text to be searched _(required)_
* `language`: Source language of the text _(required)_
* `source_id`: An identifier of the input text (e.g., a post ID on Bridge)
* `target_languages`: List of comma-separated target languages in 2-letters code (defaults to all languages in config.yml)

**Response**

200: Terms from the dictionary
```json
{
  "type": "term",
  "data": [
    {
      "_index": "glossary_mlg",
      "_type": "glossary",
      "_id": "0fa857362d489d05d8b83c64d868c21c",
      "_score": 0.5643565,
      "_source": {
        "term": "table",
        "lang": "en",
        "definition": "Sheet of slate; for writing with chalk",
        "translations": [
          {
            "lang": "pt",
            "definition": "Quadro negro, quadro ou lousa é uma superfície reusável onde se escreve textos ou desenhos que são feitos com giz ou outros marcadores apagáveis.",
            "term": "Quadro_negro"
          },
          {
            "lang": "ar",
            "definition": "تصغير|مدرس يكتب على سبورة في المدرسة السبورة أو اللوحة الدراسية هي سطح يتم الكتابة أو الرسم عليه بالطبشور ، وتستخدم عادة في التعليم.",
            "term": "سبورة"
          },
          {
            "lang": "es",
            "definition": "Una pizarra, pizarrón o encerado es una superficie de escritura reutilizable en la cual el texto o figuras se realizan con tiza u otro tipo de rotuladores borrables.",
            "term": "pizarra"
          },
          {
            "lang": "id",
            "definition": "Papan tulis adalah papan dari kayu dengan permukaan yang bisa ditulis ulang dengan menggunakan kapur tulis.",
            "term": "papan_tulis"
          },
          {
            "lang": "hi",
            "definition": "श्यामपट, जिसे चाकपट भी कहते हैं, का प्रयोग लिखने के लिए एक सतह के रूप में किया जाता है।",
            "term": "श्यामपट"
          },
          {
            "lang": "fa",
            "definition": "برای فیلی به همین نام تخته سیاه را ببینید.",
            "term": "تخته_سیاه"
          },
          {
            "lang": "tl",
            "definition": "",
            "term": "chalkboard"
          },
          {
            "lang": "tr",
            "definition": "",
            "term": "kara_tahta"
          },
          {
            "lang": "zh",
            "definition": "",
            "term": "黑板"
          }
        ],
        "context": {
          "data_source": "dictionary",
          "source_id": "x"
        },
        "en": "table"
      }
    },
    {
      "_index": "glossary_mlg",
      "_type": "glossary",
      "_id": "2c094aa2406cdad1ecb0ad4ba8a6193f",
      "_score": 0.20786226,
      "_source": {
        "term": "book ",
        "lang": "en",
        "definition": "A written work or composition that has been published (printed on pages bound together)",
        "translations": [
          {
            "lang": "pt",
            "definition": "Livro é um volume transportável, composto por páginas encadernadas, contendo texto manuscrito ou impresso e/ou imagens e que forma uma publicação unitária ou a parte principal de um trabalho literário, científico ou outro.",
            "term": "livro"
          },
          {
            "lang": "ar",
            "definition": "تصغير|الکتب الكِتابُ وجمعه الكُتبُ هي أوعية المعلومات غير الدورية والتي بطبيعة محتوياتها وتنظيمها وضعت لتُقرأ من أولها لآخرها في تتابع منطقي ولكل منها عنوان محدد حتى ولو صدرت مجمعة تحت سلسلة ما.",
            "term": "كتاب"
          },
          {
            "lang": "es",
            "definition": "Un libro es una obra impresa, manuscrita o pintada en una serie de hojas de papel, pergamino, vitela u otro material, unidas por un lado y protegidas con tapas, también llamadas cubiertas.",
            "term": "libro"
          },
          {
            "lang": "id",
            "definition": "Buku adalah kumpulan kertas atau bahan lainnya yang dijilid menjadi satu pada salah satu ujungnya dan berisi tulisan atau gambar.",
            "term": "buku"
          },
          {
            "lang": "hi",
            "definition": "पुस्तक या किताब लिखित या मुद्रित पेजों के संग्रह को कहते हैं।",
            "term": "पुस्तक"
          },
          {
            "lang": "fa",
            "definition": "بندانگشتی|کتاب‌ها کتاب مجموعه‌ای از صفحات نوشته شده، مصور، چاپ شده یا صفحات خالی ؛ ساخته شده از جوهر، کاغذ ، پوست حیوانات یا مواد دیگر می‌باشد، که معمولا\" از یک طرف یا سمت به یکدیگر محکم شده یا متصل می‌گردند. هر صفحه در کتاب ، ورق و هر سمت یا یک روی هر ورق ، صفحه نامیده می‌شود.",
            "term": "کتاب"
          },
          {
            "lang": "tl",
            "definition": "Ang aklat o tinatawag ding libro ay mga pinagsamasamang mga nailimbag na salita sa papel.",
            "term": "aklat"
          },
          {
            "lang": "tr",
            "definition": "Kitap, bir kenarından birleştirilerek dışına kapak takılmış yani ciltlenmiş, üzeri baskılı sayfaların toplamıdır.",
            "term": "kitap"
          },
          {
            "lang": "zh",
            "definition": "带有文字和图像的纸张的集合",
            "term": "书"
          }
        ],
        "context": {
          "data_source": "dictionary",
          "source_id": "x"
        },
        "en": "book "
      }
    }
  ]
}
```

400: Missing parameters
```json
{
  "type": "error",
  "data": {
    "message": "Parameters missing",
    "code": 2
  }
}
```

400: Invalid language format
```json
{
  "type": "error",
  "data": {
    "message": "Language must be in 2-letters format",
    "code": 4
  }
}
```

401: Access denied
```json
{
  "type": "error",
  "data": {
    "message": "Unauthorized",
    "code": 1
  }
}
```


#### GET /api/mt

Use this method in order to get a machine translation for a text, given source and target languages

**Parameters**

* `text`: Original text _(required)_
* `from`: Source language (two-letters code) _(required)_
* `to`: Target languages (two-letters code) _(required)_

**Response**

200: Machine translation
```json
{
  "type": "mt",
  "data": "Isso é um teste"
}
```

400: Some parameter is missing
```json
{
  "type": "error",
  "data": {
    "message": "Please provide text, source language and target language",
    "code": 2
  }
}
```

400: Language not supported
```json
{
  "type": "error",
  "data": {
    "message": "Language not supported",
    "code": 4
  }
}
```

401: Access denied
```json
{
  "type": "error",
  "data": {
    "message": "Unauthorized",
    "code": 1
  }
}
```


#### GET /api/mt/languages

Use this method in order to get a list of all languages supported for machine translation, in two-letters code

**Parameters**


**Response**

200: Supported languages
```json
{
  "type": "languages",
  "data": [
    "ar",
    "bs-Latn",
    "bg",
    "ca",
    "zh-CHS",
    "zh-CHT",
    "hr",
    "cs",
    "da",
    "nl",
    "en",
    "et",
    "fi",
    "fr",
    "de",
    "el",
    "ht",
    "he",
    "hi",
    "mww",
    "hu",
    "id",
    "it",
    "ja",
    "sw",
    "tlh",
    "tlh-Qaak",
    "ko",
    "lv",
    "lt",
    "ms",
    "mt",
    "yua",
    "no",
    "otq",
    "fa",
    "pl",
    "pt",
    "ro",
    "ru",
    "sr-Cyrl",
    "sr-Latn",
    "sk",
    "sl",
    "es",
    "sv",
    "th",
    "tr",
    "uk",
    "ur",
    "vi",
    "cy"
  ]
}
```

401: Access denied
```json
{
  "type": "error",
  "data": {
    "message": "Unauthorized",
    "code": 1
  }
}
```


## Rake tasks

There are rake tasks for a few tasks (besides Rails' default ones). Run them this way: `bundle exec rake <task name>`

* `test:coverage`: Run all tests and calculate test coverage
* `application=<application name> lapis:api_keys:create`: Create a new API key for an application
* `lapis:api_keys:delete_expired`: Delete all expired keys
* `lapis:error_codes`: List all error codes that this application can return
* `lapis:licenses`: List the licenses of all libraries used by this project
* `lapis:client:ruby`: Generate a client Ruby gem, that allows other applications to communicate and test this service
* `lapis:client:php`: Generate a client PHP library, that allows other applications to communicate and test this service
* `lapis:docs`: Generate the documentation for this API, including models and controllers diagrams, Swagger, API endpoints, licenses, etc.
* `lapis:docker:run`: Run the application in Docker
* `lapis:docker:shell`: Enter the Docker container
* `swagger:docs:markdown`: Generate the documentation in markdown format

## Troubleshooting

### Exception `RubyPython::InvalidInterpreter: An invalid interpreter was specified` when running `bundle exec rake db:migrate`
This is because RubyPython [hardcodes the list of locations to search for `libpython`](https://github.com/halostatue/rubypython/blob/master/lib/rubypython/interpreter.rb#L81). To fix:

* Identify your default Python version: `python --version`. You get something like:
```
Python 2.7.6
```
* Find your corresponding `libpython` library: `find /usr/lib -name 'libpython2.7*'`. You get something like:
```
/usr/lib/python2.7/config-x86_64-linux-gnu/libpython2.7.so
/usr/lib/python2.7/config-x86_64-linux-gnu/libpython2.7.a
/usr/lib/python2.7/config-x86_64-linux-gnu/libpython2.7-pic.a
/usr/lib/x86_64-linux-gnu/libpython2.7.so
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0
/usr/lib/x86_64-linux-gnu/libpython2.7.a
```
* Symlink the `.so` library to one of the locations that RubyPython will check: `sudo ln -s /usr/lib/python2.7/config-x86_64-linux-gnu/libpython2.7.so /usr/lib/`

* Try again, issue should be fixed!
