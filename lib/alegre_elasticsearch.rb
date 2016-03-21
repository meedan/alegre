require 'rubypython'
require 'json'
require 'elasticsearch'

GLOSSARY_INDEX = CONFIG['glossary_index']
GLOSSARY_TYPE  = CONFIG['glossary_type']
ES_SERVER = CONFIG['elasticsearch_server'].to_s + ':' + CONFIG['elasticsearch_port'].to_s

module Alegre
  class ElasticSearch

    def self.delete_glossary(_id)
      client = Elasticsearch::Client.new log: true, url: ES_SERVER

      if client.exists? index: GLOSSARY_INDEX, type: GLOSSARY_TYPE, id: _id
        client.delete index: GLOSSARY_INDEX, type: GLOSSARY_TYPE, id: _id
        client.indices.refresh index: GLOSSARY_INDEX
        return true
      else
        return false
      end
    end

    def self.get_glossary(str)
      client = Elasticsearch::Client.new log: true, url: ES_SERVER
      glossary = []
      data_hash = JSON.parse(str)
      query = self.buildQuery(data_hash)

      begin
        ret = client.search index: GLOSSARY_INDEX, type: GLOSSARY_TYPE, body: query
        for doc in ret['hits']['hits']
          glossary << doc
        end
      rescue Exception => e
        puts 'Exception in get_glossary: ' + e.message
      end

      return glossary
    end

    def self.add_glossary(jsonStr, should_replace = 0)
      client = Elasticsearch::Client.new log: true, url: ES_SERVER
      begin
        data_hash = JSON.parse(jsonStr)
        if self.validationInsert(data_hash)
          data_hash = self.updateTermName (data_hash)
          _id = self.generate_id_for_glossary_term(data_hash)
          exists = client.exists?(index: GLOSSARY_INDEX, type: GLOSSARY_TYPE, id: _id)
          replace = should_replace.to_i === 1
          if !exists || replace
            str = data_hash.to_s.gsub("=>", ':')

            client.index index: GLOSSARY_INDEX,
            type: GLOSSARY_TYPE,
            id: _id,
            body: str

            client.indices.refresh index: GLOSSARY_INDEX
          end
          return true
        else
          return false
        end
      rescue Exception => e
        return false
      end
    end

    def self.buildQuery(jsonCtx)
      dQuery = []
      dContext = []
      jsonDc = {}
      lang = ''

      if jsonCtx.has_key?('post') and !jsonCtx.has_key?('term')
        jsonCtx["term"] = jsonCtx["post"]
        jsonCtx["post"] = nil
      end

      if !jsonCtx.has_key?('lang')
        lang = Alegre::Dysl.new.try_to_classify(jsonCtx["term"])
        if lang.length > 0
          jsonCtx['lang'] =  lang[0][1]
        end
      end

      term = jsonCtx["lang"]

      if jsonCtx[term].nil?
        jsonCtx[term] = jsonCtx["term"]
        jsonCtx["term"] = nil
      end

      jsonCtx.each do |key, value|
      #2 levels {u'source': {u'url': u'testSite.url', u'name': u'test site'}, u'post': u'lala lala', u'data_source': u'dictionary'}
      if (!value.nil? && !key.nil?)
        object = value
        if String === object
          if (key != "context") or !(value.class is Int)
            dQuery << '{"match": {"'+key+'": "'+value+'"}}'
          end
        elsif Hash === object
          value.each do |k, v|
            if Hash === v   #context (2o level)
              v.each do |kk, vv|
                dQuery << '{"match": {"'+key+"."+k+"."+kk+'": "'+vv+'"}}'
              end
            elsif Array === v
              for n in v
                dQuery << '{"query_string" : {"fields" : ["'+key+"."+k+'"],"query" : "'+n+'"} }'
              end
            else
              dQuery << '{"match": {"'+key+"."+k+'": "'+v+'"}}'
            end
          end
        end
      end
    end

    sQuery = dQuery.to_s
    sQuery = sQuery.gsub '", "', ','
    sQuery = sQuery.gsub '["{', '[{'
    sQuery = sQuery.gsub '}"]', '}]'
    sQuery = sQuery.gsub "\\",""

    if (dQuery.length  > 0)
      dc = '{"query": {"bool": {"must": '+ sQuery +'}}}'
    end

    return dc
  end

  def self.generate_id_for_glossary_term(t)
    id = [t['term'], t['lang'], t['translations'].collect{ |x| x['lang'] }, t['context']].inspect
    return Digest::MD5.hexdigest(id)
  end

  def self.updateTermName (jsonDoc)
    term = jsonDoc["lang"]

    if jsonDoc[term].nil?
      jsonDoc[term] = jsonDoc["term"]
    end
    return jsonDoc
  end

  def self.validationInsert (jsonDoc)
    if !jsonDoc["lang"].nil?
      term = jsonDoc["lang"]

      if !jsonDoc[term].nil? or !jsonDoc['term'].nil?
        return true
      else
        return false
      end
    else
      return false
    end
  end

  def self.create_index
    client = Elasticsearch::Client.new log: true, url: ES_SERVER

    if client.indices.exists? index: GLOSSARY_INDEX
      client.indices.delete index: GLOSSARY_INDEX
    end

    client.indices.create index: GLOSSARY_INDEX, body: Alegre::ElasticSearch.schema
  end

  def self.schema
    '{"mappings": {
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
    end
  end
end
