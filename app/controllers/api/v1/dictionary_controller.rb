#encoding: utf-8 
require "net/http"
require 'json'
require 'mlg_elastic_search'
require 'retriable'


KEY = CONFIG['babelfy_key'] 
LANGCODES = CONFIG['langcodes'] 

class Api::V1::DictionaryController < Api::V1::BaseApiController

include DictionaryDoc

def execute() #POST

    if params[:language].blank? or params[:text].blank?
        render_parameters_missing
    elsif params[:language].length != 2
	      render_error('invalid value', 'INVALID_VALUE', status = 400)
    else
	begin
		text = params[:text].to_s
		codesource = params[:language].to_s

		if !params[:postid].nil?
			postid = params[:postid]
		else
			postid = ""
		end

		uri = URI("https://babelfy.io/v1/disambiguate?")

		#segments have three attributes: text, language and offset
	
		params = {
		  :text => text,
		  :lang  => codesource,
		  :key  => 'KEY'
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
				LANGCODES.each do |lang|
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
					payload = generatePayload(codesource.downcase, sourceterm, sourcedefinition, translations, postid)
					retES = Mlg::ElasticSearch.add_glossary(payload)
				end
			

			end
		      end
		      render_success 'success', true
		end
	
	rescue Exception => msg  
	      render_error(msg, 'INVALID_VALUE', status = 400)
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
		  #p json

		end
	end
	return json
end


#return the first sense in the language as main
def GetMainSense(by,lang) 
	by['senses'].each do |entry|
		if entry['language'] == lang
			return entry
		end
	end
	return {}
end

def GetMainGloss(by,lang)
	by['glosses'].each do |entry|
		if entry['language'] == lang
			return entry
		end
	end
	return {}
end

def generatePayload(codesource, sourceterm, sourcedefinition, translations, postid)
	if postid.length > 0
		contextStr =  '{"post": "'+postid+'","data_source": "dictionary"}'
	else
		contextStr =  '{"data_source": "dictionary"}'
	end
	strTranslations = translations.to_s.gsub("=>",":")
	strJson = '{"term": "'+sourceterm+'", "lang": "'+codesource+'", "definition": "'+sourcedefinition+'","translations": '+strTranslations+',"context":'+contextStr+'}'
	return strJson
end


end
