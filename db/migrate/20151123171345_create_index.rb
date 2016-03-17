require 'elasticsearch'
require 'alegre_elasticsearch'

class CreateIndex < ActiveRecord::Migration
  def change
    Alegre::ElasticSearch.create_index
  end
end

