#encoding: utf-8 
# :nocov:
module GlossaryDoc
  extend ActiveSupport::Concern
 
  included do
    swagger_controller :glossary, 'Glossary'
 #### Get terms from glossary
    swagger_api :terms do
      summary 'Get terms from a post'
      notes 'Use this method in order to get terms from glossary'
      param :query, :data, :string, :required, '{"post":"test the app","context": {"source": {"url": "testSite.url","name": "test site"}}}'
      response :ok, '{ "type": "term", "data": [{ "_score" : "6.837847", "_id" : "312826213161669685473612972876928820074", "_source:", "lang" : "en", "definition" : "test definition", "term" : "test", "translations:["lang" : "pt", "definition" : "definição de teste", "term" : "teste"], "context: {"source:"{"url" : "testSite.url", "name" : "test site"}, "time-zone" : "PDT / MST", "tags:["greetings", "hello"], "post" : "xxxx", "page_id" : "test", "data_source" : "dictionary"}, "_index" : "glossary_mlg , "_type" : "glossary"}]}'
      response 400, 'Parameters missing (data was not provided)'
      response 401, 'Access denied'
    end

    #### Add term to glossary
    swagger_api :term do
      summary 'Add term to glossary'
      notes 'Use this method in order to add a new term to glossary'
      param :query, :data, :string, :required, '{"term": "test", "lang": "en", "definition": "test definition","translations": [ {"lang": "pt","definition": "definição de teste","term": "teste"}],"context": {"source": {"url": "testSite.url","name": "test site"},"page_id":"test", "post": "xxxx","data_source": "dictionary","time-zone": "PDT / MST"}}'
      response :ok, 'Success'
      response 400, 'Error'
      response 401, 'Access denied'
    end

    #### Delete term to glossary
    swagger_api :delete do
      summary 'Delete term from glossary'
      notes 'Use this method in order to delete a term from glossary'
      param :query, :id, :string, :required, '1234567898'
      response :ok, 'Success'
      response 400, 'Error'
      response 401, 'Access denied'
    end

  end
end
# :nocov:
