#encoding: utf-8 
require 'json'
require 'elasticsearch'
require 'rubypython'

class Api::V1::GlossaryController < Api::V1::BaseApiController

  include GlossaryDoc

  GLOSSARY_INDEX = "glossary_mlg"
  GLOSSARY_TYPE = "glossary"
  LANG_WITH_ANALYZER = ['ar', 'hy', 'eu', 'pt', 'bg', 'ca', 'zh', 'cs', 'da', 'nl', 'en', 'fi', 'fr', 'gl', 'de', 'el', 'hi', 'hu', 'id', 'ga', 'it', 'lv', 'no', 'fa', 'pt', 'ro', 'ru', 'ckb', 'sp', 'sv', 'tr', 'th'] #languages with stem and stop analyzers in elasticsearch index

  def term #POST
    if params[:data].blank?
      render_parameters_missing
    else
	client = Elasticsearch::Client.new log: true

	#begin
		str = params[:data].to_s
		data_hash = JSON.parse(str)
	

		v  = validationInsert(data_hash)
		
		if validationInsert(data_hash)
			p "A"
			if !exist_glossary_term(data_hash)
				p "B"
				str = str.gsub("\\", '')

				_id = generate_id_for_glossary_term(data_hash)
				p _id
				client.index index: GLOSSARY_INDEX,
					     type: GLOSSARY_TYPE,
					     id: _id,
					     body: str
					    


				render_success 'term', '@glossary'
			else
			      render_error(msg, 'DUPLICATED', status = 400)
			end
		else
		      render_error(msg, 'MISSING_PARAMETERS', status = 400)
		end
	#rescue Exception => msg  
	#      render_error(msg, 'INVALID_VALUE', status = 400)
	#end  


    end
  end

  def terms #GET
    if params[:data].blank?
      render_parameters_missing
    else
	client = Elasticsearch::Client.new log: true

	#begin
		str = params[:data].to_s
		data_hash = JSON.parse(str)
		query = buildQuery (data_hash)
		ret = client.search index: GLOSSARY_INDEX, type: GLOSSARY_TYPE, body: query

		@glossary = Array.new

		for doc in ret['hits']['hits']
			@glossary << doc.to_s
		end
		render_success 'term', @glossary
	#rescue Exception => msg  
	#      render_error(msg, 'INVALID_VALUE', status = 400)
	#end  
    end
   end

    def generate_id_for_glossary_term(data_hash)
  	str = 'glossary'+":"+  data_hash["term"].to_s+":"+ data_hash["lang"].to_s
	if !data_hash["context"]["source"]["name"].nil?
	  	str = str + ":"+  data_hash["context"]["source"]["name"]
	end
	if !data_hash["context"]["page_id"].nil?
	  	str = str + ":"+  data_hash["context"]["page_id"]
	end
	id = Digest::MD5.hexdigest(str)
	return (id)
    end
    
    def validationInsert (jsonDoc)
	begin
		if !jsonDoc["term"].nil? and !jsonDoc["lang"].nil?
			return true
		else		
			return false
		end
	rescue Exception => msg  
	      return false
	end  

    end

   def exist_glossary_term(data_hash)
	client = Elasticsearch::Client.new log: true

	begin
		str = params[:data].to_s
		_id = generate_id_for_glossary_term(data_hash)
		query ='{"query":{ "ids":{ "values": ["'+_id+'"] } } }'
		ret = client.search index: GLOSSARY_INDEX, type: GLOSSARY_TYPE, body: query
		if (ret['hits']['hits'].length  > 0)
			return true
		else
			return false
		end

	rescue Exception => msg  
		return false
	end  



    end

    def buildQuery (jsonCtx)
	dQuery = []	
	dContext = []
	jsonDc = {}
	lang = ''

	if jsonCtx.has_key?('post') and !jsonCtx.has_key?('term')
		jsonCtx["term"] = jsonCtx["post"]
		jsonCtx["post"] = nil
	end
	p jsonCtx
	if !jsonCtx.has_key?('lang')
			lang = DYSL.classifyReturnAll(jsonCtx["term"],STOPWORDS_PATH).rubify
			if lang.length > 0
		    		jsonCtx['lang'] =  lang[0][1]
			end
	end

	if (jsonCtx.has_key?('lang')) and (LANG_WITH_ANALYZER.include? jsonCtx['lang'])
		analyzer = "analyzer_"+jsonCtx['lang']+"_stem"
	else
		analyzer = "default"
	end


	jsonCtx.each do |key, value|
	    #2 levels {u'source': {u'url': u'testSite.url', u'name': u'test site'}, u'post': u'lala lala', u'data_source': u'dictionary'}
	    if (!value.nil?)
		object = value
		if String === object
			if (key == "term")
				dQuery << '{"match": {"term": {"query": "'+value+'", "analyzer": "'+analyzer+'"}}}'
			else
				if (key != "context") or !(value.class is Int)
					dQuery << '{"match": {"'+key+'": "'+value+'"}}'
				end
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
	sQuery = sQuery.gsub! '", "', ','
	sQuery = sQuery.gsub! '["{', '[{'
	sQuery = sQuery.gsub! '}"]', '}]'
	sQuery = sQuery.gsub! "\\",""

	if (dQuery.length  > 0)
		dc = '{"query": { "bool": { "must": '+ sQuery +'}}}'
					p "KJKJKJ"
		p dc
					p "KJKJKJ"
	end

	
	return dc


  end


end
