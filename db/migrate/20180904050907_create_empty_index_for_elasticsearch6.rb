require 'elasticsearch'
require 'alegre_elasticsearch'

class CreateEmptyIndexForElasticsearch6 < ActiveRecord::Migration
  def change
    Alegre::ElasticSearch.create_index
  end
end

