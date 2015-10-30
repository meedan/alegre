#encoding: utf-8 
# :nocov:
module GlossaryDoc
  extend ActiveSupport::Concern
 
  included do
    swagger_controller :glossary, 'Glossary'

    #### Add and Get term to glossary
    swagger_api :term do
      summary 'Add (Post) and Get term'
      notes 'Use this method in order to add a new term to glossary'
      param :query, :data, :string, :required, 'POST : {"lang": "en", "definition": "test definition","term": "test","translations": [ {"lang": "pt","definition": "definição de teste","term": "teste"}],"context": {"post": "post", "source": {"url": "testSite.url","name": "test site"},"post": "xxxx","data_source": "dictionary","time-zone": "PDT / MST"},"page_id":"test", "data_source": "dictionary" } ; GET : {"term":"hello","context": {"source": {"url": "testSite.url","name": "test site"}, "post": "lala lala", "data_source": "dictionary"}}'
      response :ok, 'POST: Success; GET: { "type": "term", "data": { "_score" : "6.837847", "_id" : "312826213161669685473612972876928820074", "_source:", "lang" : "en", "definition" : "test definition", "term" : "test", "translations:["lang" : "pt", "definition" : "definição de teste", "term" : "teste"], "context: {"source:"{"url" : "testSite.url", "name" : "test site"}, "time-zone" : "PDT / MST", "tags:["greetings", "hello"], "post" : "xxxx", "page_id" : "test", "data_source" : "dictionary"}, "_index" : "glossary_mlg , "_type" : "glossary"}}'
      response 400, 'Parameters missing (text was not provided)'
      response 401, 'Access denied'
    end

  end
end
# :nocov:
