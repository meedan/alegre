require 'elasticsearch'
require 'alegre_elastic_search'

class CreateIndex < ActiveRecord::Migration
  def change
    Alegre::ElasticSearch.create_index
  end
end

