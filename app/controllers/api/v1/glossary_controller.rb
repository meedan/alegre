#encoding: utf-8 
require 'mlg_elastic_search'

class Api::V1::GlossaryController < Api::V1::BaseApiController

  include GlossaryDoc

  GLOSSARY_INDEX = CONFIG['glossary_index'] 
  GLOSSARY_TYPE  = CONFIG['glossary_type'] 
  ES_SERVER = CONFIG['elasticsearch_server'].to_s + ':' + CONFIG['elasticsearch_port'].to_s
  LANG_WITH_ANALYZER = CONFIG['lang_with_analyzer']  #languages with stem and stop analyzers in elasticsearch index

  def term # POST
    if params[:data].blank?
      render_parameters_missing
    else
      str = params[:data].to_s
      retES = Mlg::ElasticSearch.add_glossary(params[:data].to_s)
      if retES
        render_success 'success', true
      else
        render_error("ES Error", 'MISSING_PARAMETERS', status = 400)
      end
    end
  end

  def terms # GET
    if params[:data].blank?
      render_parameters_missing
    else
      client = Elasticsearch::Client.new log: true, url: ES_SERVER

      @glossary = Mlg::ElasticSearch.get_glossary(params[:data].to_s)
      
      render_success 'term', @glossary
    end
  end

  def delete # DELETE
    if params[:id].blank?
      render_parameters_missing
    else
      ret = false
      ret = Mlg::ElasticSearch.delete_glossary(params[:id].to_s)
      if ret
        render_success 'delete', true
      else
        render_error('Could not delete', 'INVALID_VALUE', status = 400)
      end
    end
  end
end
