## MLG API

A REST API to Meedan's linguistic functionality.

## Installation

* Copy `config/config.yml.example` to `config/config.yml` and adjust the options
* Copy `config/database.yml.example` to `config/database.yml` and adjust the options
* Copy `config/initializers/secret_token.rb.example` to `config/initializers/secret_token.rb` and adjust the options
* Copy `config/initializers/errbit.rb.example` to `config/initializers/errbit.rb` and adjust the options
* Update `config/initializers/train.rb` to add model file, stopwords files and DYSL paths
* Run `bundle install` to install dependencies
* Run `bundle exec rake db:migrate` to create database schema
* Run `bundle exec rake lapis:api_keys:create` to create API key
* Run `bundle exec rake swagger:docs` to generate web-based documentation
* Run `cd doc && make` to generate full documentation
* Run `rails s` and access API at http://localhost:3000/api

## Features

### Language identification

#### Add training sample to a model file

Format: POST /api/languages/sample

`curl -X POST http://localhost:3000/api/languages/sample -d '{"text":"this is a new sample","language":"en"}' -H "Content-Type: application/json"`

Returns:

`{
  "type": "success",
  "data": true
}`

In order to use this method, you need to have the corpus files inside the API server.

#### List supported languages in a model

Format: GET /api/languages/language

`curl -X GET http://localhost:3000/api/languages/language -H "Content-Type: application/json" -H 

Returns:

`{ "type": "language_code", "data": ["en","pt","es","ar"]}`


#### Language Identification

Format: GET /api/languages/identification

`curl -X GET http://localhost:3000/api/languages/identification -d '{"text":"what is my language?"}' -H "Content-Type: application/json" 

Returns:

`{
  "type": "language",
  "data": [
    [
      0.9556870372582787,
      "en"
    ],
    [
      0.04431296274172125,
      "ms"
    ]
  ]
}`

### Glossary

#### Get term from glossary

Format: GET /api/glossary/terms

`curl -X GET http://localhost:3000/api/glossary/terms -d '{"post":"test the app","context": {"source": {"url": "testSite.url","name": "test site"}}}' -H "Content-Type: application/json"`

Returns:

`'{ "type": "term", 
  "data": [
     { "_score" : "6.837847", 
	"_id" : "312826213161669685473612972876928820074", 
	"_source:", 
	"lang" : "en", 
	"definition" : "test definition", 
	"term" : "test", 
	"translations:["lang" : "pt", "definition" : "definição de teste", "term" : "teste"], "context: {"source:"{"url" : "testSite.url", "name" : "test site"}},
	 "_index" : "glossary_mlg , 
	"_type" : "glossary"}
  ]
}`

#### Add term to glossary

Format: POST /api/glossary/term

`curl -X POST http://localhost:3000/api/glossary/term -d '{"lang": "en", "definition": "test definition","term": "test","translations": [ {"lang": "pt","definition": "definição de teste","term": "teste"}],"context": {"post": "post", "source": {"url": "testSite.url","name": "test site"},"time-zone": "PDT / MST","page_id":"test"} }' -H "Content-Type: application/json"`

Returns:

`{
  "type": "success",
  "data": true
}`

#### Delete term from glossary

Format: POST /api/glossary/delete

`curl -X POST http://localhost:3000/api/glossary/delete -d '{"id": "ef3327927388e480149e719836d0ce03" }' -H "Content-Type: application/json"`

Returns:

`{
  "type": "success",
  "data": true
}`
