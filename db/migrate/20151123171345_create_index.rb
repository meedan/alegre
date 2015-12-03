require 'elasticsearch'

GLOSSARY_INDEX = CONFIG['glossary_index'] 
GLOSSARY_TYPE  = CONFIG['glossary_type'] 
ES_SERVER = CONFIG['elasticsearch_server'].to_s + ':' + CONFIG['elasticsearch_port'].to_s

class CreateIndex < ActiveRecord::Migration
  def change
    return if ES_SERVER === ':'

    Elasticsearch::Client.new url: ES_SERVER
    client = Elasticsearch::Client.new log: true

    
    if client.indices.exists? index: GLOSSARY_INDEX

      client.indices.delete index: GLOSSARY_INDEX
    end  

 
	str = '{"mappings": {
         "glossary": {
            "properties": {
               "ar": {
                  "type": "string",
                  "analyzer": "arabic"
               },
               "bg": {
                  "type": "string",
                  "analyzer": "bulgarian"
               },
               "ca": {
                  "type": "string",
                  "analyzer": "catalan"
               },
               "cs": {
                  "type": "string",
                  "analyzer": "czech"
               },
               "da": {
                  "type": "string",
                  "analyzer": "danish"
               },
               "de": {
                  "type": "string",
                  "analyzer": "german"
               },
               "el": {
                  "type": "string",
                  "analyzer": "greek"
               },
               "en": {
                  "type": "string",
                  "analyzer": "english"
               },
               "es": {
                  "type": "string",
                  "analyzer": "spanish"
               },
               "eu": {
                  "type": "string",
                  "analyzer": "basque"
               },
               "fa": {
                  "type": "string",
                  "analyzer": "persian"
               },
               "fi": {
                  "type": "string",
                  "analyzer": "finnish"
               },
               "fr": {
                  "type": "string",
                  "analyzer": "french"
               },
               "ga": {
                  "type": "string",
                  "analyzer": "irish"
               },
               "gl": {
                  "type": "string",
                  "analyzer": "galician"
               },
               "hi": {
                  "type": "string",
                  "analyzer": "hindi"
               },
               "hu": {
                  "type": "string",
                  "analyzer": "hungarian"
               },
               "hy": {
                  "type": "string",
                  "analyzer": "armenian"
               },
               "id": {
                  "type": "string",
                  "analyzer": "indonesian"
               },
               "it": {
                  "type": "string",
                  "analyzer": "italian"
               },
               "lv": {
                  "type": "string",
                  "analyzer": "latvian"
               },
               "nl": {
                  "type": "string",
                  "analyzer": "dutch"
               },
               "no": {
                  "type": "string",
                  "analyzer": "norwegian"
               },
               "pt": {
                  "type": "string",
                  "analyzer": "brazilian"
               },
               "ro": {
                  "type": "string",
                  "analyzer": "romanian"
               },
               "ru": {
                  "type": "string",
                  "analyzer": "russian"
               },
               "sv": {
                  "type": "string",
                  "analyzer": "swedish"
               },
               "term": {
                  "type": "string"
               },
               "th": {
                  "type": "string",
                  "analyzer": "thai"
               },
               "tr": {
                  "type": "string",
                  "analyzer": "turkish"
               },
               "zh": {
                  "type": "string",
                  "analyzer": "chinese"
               }
            }
         }
      }}'

    client.indices.create index: GLOSSARY_INDEX, body: str

  end
end

