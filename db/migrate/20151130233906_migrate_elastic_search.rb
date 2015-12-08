require 'elasticsearch'

GLOSSARY_INDEX = CONFIG['glossary_index'] 
GLOSSARY_TYPE  = CONFIG['glossary_type'] 
ES_SERVER = CONFIG['elasticsearch_server'].to_s + ':' + CONFIG['elasticsearch_port'].to_s
OLD_GLOSSARY_INDEX = CONFIG['glossary_index_old'] 
OLD_GLOSSARY_TYPE  = '.percolator' 
OLD_ES_SERVER = CONFIG['elasticsearch_server_old'].to_s + ':' + CONFIG['elasticsearch_port_old'].to_s


class MigrateElasticSearch < ActiveRecord::Migration
  def change
  return if ES_SERVER === ':'
	Elasticsearch::Client.new url: ES_SERVER
	client = Elasticsearch::Client.new log: true

	ret = client.search index: OLD_GLOSSARY_INDEX, type: OLD_GLOSSARY_TYPE,  size: 10000, body: { query: { match_all: {} } }
	
	n = 1
	for doc in ret['hits']['hits']
		new_data = Hash.new
		new_data['context']  = Hash.new
		_id = doc['_id']
		doc['_source'].each {|key, value| 
			case key
			when "definition"
				new_data['definition'] = value
			when "dictionary"
				if value.has_key?("translations")
					new_data['translations'] = value['translations']
				end
			when "query"
				value["filtered"]["query"]["match"].each {|k, v| 					
						new_data['term'] = value["filtered"]["query"]["match"][k]['query']
						new_data['lang'] = k
				}
			else
				new_data['context'][key] = value
			end
		}

		new_data[new_data['lang']] = new_data['term']
		str = new_data.to_s.gsub("=>", ':')

		#p n
		n = n + 1
		client.index index: GLOSSARY_INDEX,
			     type: GLOSSARY_TYPE,
			     id: _id,
			     body: str
			    

	end


  end
end
