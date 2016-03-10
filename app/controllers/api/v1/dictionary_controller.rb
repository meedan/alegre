#encoding: utf-8 
require "net/http"
require 'json'
require 'alegre_elastic_search'
require 'retriable'

KEY = CONFIG['babelfy_key'] 
LANGCODES = CONFIG['langcodes'] 

class Api::V1::DictionaryController < Api::V1::BaseApiController

  include DictionaryDoc

  def terms
    if params[:language].blank? or params[:text].blank?
      render_parameters_missing
    elsif params[:language].length != 2
      render_error('Language must be in 2-letters format', 'INVALID_VALUE', 400)
    else
      client = Elasticsearch::Client.new log: true, url: ES_SERVER
      context = { source_id: params[:source_id].to_s }
      context[:target_languages] = params[:target_languages] unless params[:target_languages].blank?
      data = { lang: params[:language], term: params[:text], context: context }

      @dictionary = Alegre::ElasticSearch.get_glossary(data.to_json)
      @babelfy_requested = false
      
      if @dictionary.empty?
        request_terms
        @babelfy_requested = true
        @dictionary = Alegre::ElasticSearch.get_glossary(data.to_json)
      end

      render_success 'term', @dictionary
    end    
  end

  private

  def request_terms
    text = params[:text].to_s
    codesource = params[:language].to_s
    codetargets = params[:target_languages].blank? ? LANGCODES : (params[:target_languages].upcase.split(',') | [codesource.upcase])

    uri = URI("https://babelfy.io/v1/disambiguate?")

    #segments have three attributes: text, language and offset

    params = {
      :text => text,
      :lang  => codesource,
      :key  => KEY
    }

    uri.query = URI.encode_www_form(params)

    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true

    Retriable.retriable do  
      response = http.request(Net::HTTP::Get.new(uri.request_uri))

      if response.is_a?(Net::HTTPSuccess)
        json = JSON.parse(response.body)

        json.each do |annotation|

          sourceterm = text[annotation["charFragment"]["start"]..annotation["charFragment"]["end"]+1]
          sourcedefinition= ""
          translations = []
          codetargets.each do |lang|
            by = GetSynset(annotation['babelSynsetID'], lang)
            bs = GetMainSense(by,lang) 
            definition  = term = ""
            if bs.length > 0
              term = bs["simpleLemma"]
              g = GetMainGloss(by,lang) 
              if g.length > 0
                definition = g["gloss"]
              end
            end


            # Source
            if (lang.upcase  == codesource.upcase ) 
              sourcedefinition = definition;    
            elsif term.length > 0
              translation = {}
              translation["lang"] = lang.downcase 
              translation["definition"] = definition
              translation["term"] = term
              if (term != "")
                translations << translation
              end  
            end

          end
          retES = false
          if sourcedefinition.length > 0
            payload = ""
            payload = generatePayload(codesource.downcase, sourceterm, sourcedefinition, translations)
            retES = Alegre::ElasticSearch.add_glossary(payload)
          end
        end
      end
    end
  end

  def GetSynset(id, lang)
    uri = URI("https://babelnet.io/v2/getSynset?")
    json = {}

    params = {
      :id => id,
      :key  => KEY,
      :filterLangs => lang
    }

    uri.query = URI.encode_www_form(params)

    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true

    Retriable.retriable do  
      response = http.request(Net::HTTP::Get.new(uri.request_uri))

      if response.is_a?(Net::HTTPSuccess)
        json = JSON.parse(response.body)
      end
    end
    return json
  end


  #return the first sense in the language as main
  def GetMainSense(by,lang) 
    by['senses'] ||= []
    by['senses'].each do |entry|
      if entry['language'] == lang
        return entry
      end
    end
  end

  def GetMainGloss(by,lang)
    by['glosses'].each do |entry|
      if entry['language'] == lang
        return entry
      end
    end
  end

  def generatePayload(codesource, sourceterm, sourcedefinition, translations)
    contextStr =  { 'data_source' => 'dictionary' }
    contextStr['source_id'] = params[:source_id] unless params[:source_id].blank?
    contextStr['target_languages'] = params[:target_languages] unless params[:target_languages].blank?
    strTranslations = translations.to_s.gsub("=>",":")
    strJson = '{"term": "'+sourceterm+'", "lang": "'+codesource+'", "definition": "'+sourcedefinition+'","translations": '+strTranslations+',"context":'+contextStr.to_json+'}'
    Rails.logger.info "Generated payload #{strJson}"
    return strJson
  end
end
