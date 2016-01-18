require 'elasticsearch'
require 'mlg_elastic_search'

class CreateIndex < ActiveRecord::Migration
  def change
    Mlg::ElasticSearch.create_index
  end
end

