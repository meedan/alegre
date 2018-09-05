require 'rubypython'
require 'json'
require 'elasticsearch'

GLOSSARY_INDEX = CONFIG['glossary_index'] 
GLOSSARY_TYPE  = CONFIG['glossary_type'] 
ES_SERVER = CONFIG['elasticsearch_server'].to_s + ':' + CONFIG['elasticsearch_port'].to_s
LANG_WITH_ANALYZER = CONFIG['lang_with_analyzer']  #languages with stem and stop analyzers in elasticsearch index


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
      instance = langid.LangId.new(CONFIG['langid'])
      lang = instance.classify(jsonCtx["term"])
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
            dQuery << '{"match": {"' + key.to_s + '": "' + value.to_s + '"}}'
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
      dc = '{"query": { "bool": { "must": '+ sQuery +'}}}'
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
    index = CONFIG['glossary_index'] 
    es_server = CONFIG['elasticsearch_server'].to_s + ':' + CONFIG['elasticsearch_port'].to_s

    return if es_server === ':'

    client = Elasticsearch::Client.new log: true, url: es_server
    
    if client.indices.exists? index: index
      client.indices.delete index: index
    end  

    client.indices.create index: index, body: Alegre::ElasticSearch.schema
  end

  def self.schema
    '{"mappings": {
         "glossary": {
            "properties": {
               "ar": {
                  "type": "text",
                  "analyzer": "arabic"
               },
               "bg": {
                  "type": "text",
                  "analyzer": "bulgarian"
               },
               "ca": {
                  "type": "text",
                  "analyzer": "catalan"
               },
               "cs": {
                  "type": "text",
                  "analyzer": "czech"
               },
               "da": {
                  "type": "text",
                  "analyzer": "danish"
               },
               "de": {
                  "type": "text",
                  "analyzer": "german"
               },
               "el": {
                  "type": "text",
                  "analyzer": "greek"
               },
               "en": {
                  "type": "text",
                  "analyzer": "english"
               },
               "es": {
                  "type": "text",
                  "analyzer": "spanish"
               },
               "eu": {
                  "type": "text",
                  "analyzer": "basque"
               },
               "fa": {
                  "type": "text",
                  "analyzer": "persian"
               },
               "fi": {
                  "type": "text",
                  "analyzer": "finnish"
               },
               "fr": {
                  "type": "text",
                  "analyzer": "french"
               },
               "ga": {
                  "type": "text",
                  "analyzer": "irish"
               },
               "gl": {
                  "type": "text",
                  "analyzer": "galician"
               },
               "hi": {
                  "type": "text",
                  "analyzer": "hindi"
               },
               "hu": {
                  "type": "text",
                  "analyzer": "hungarian"
               },
               "hy": {
                  "type": "text",
                  "analyzer": "armenian"
               },
               "id": {
                  "type": "text",
                  "analyzer": "indonesian"
               },
               "it": {
                  "type": "text",
                  "analyzer": "italian"
               },
               "lv": {
                  "type": "text",
                  "analyzer": "latvian"
               },
               "nl": {
                  "type": "text",
                  "analyzer": "dutch"
               },
               "no": {
                  "type": "text",
                  "analyzer": "norwegian"
               },
               "pt": {
                  "type": "text",
                  "analyzer": "brazilian"
               },
               "ro": {
                  "type": "text",
                  "analyzer": "romanian"
               },
               "ru": {
                  "type": "text",
                  "analyzer": "russian"
               },
               "sv": {
                  "type": "text",
                  "analyzer": "swedish"
               },
               "term": {
                  "type": "text"
               },
               "th": {
                  "type": "text",
                  "analyzer": "thai"
               },
               "tr": {
                  "type": "text",
                  "analyzer": "turkish"
               },
               "zh": {
                  "type": "text",
                  "analyzer": "chinese"
               }
            }
         }
      }}'
    end
  end
end
