#encoding: utf-8 
# :nocov:
module GlossaryDoc
  extend ActiveSupport::Concern

  TERM = {
    term: 'Test',
    lang: 'en', 
    definition: 'An experiment',
    translations: [
      { lang: 'pt', definition: 'Um experimento', term: 'Teste' },
      { lang: 'es', definition: 'Un experimento', term: 'Teste' }
    ],
    context: { page_id: 'foo', 'data_source' => 'glossary' }
  }.to_json

  TERM_ID = '2c94a1c8dc37c8c90338739f3c779c28'

  TERM_QUERY = { lang: 'en', term: 'This is just a test', context: { page_id: 'foo' } }.to_json
 
  included do
    swagger_controller :glossary, 'Glossary'

    swagger_api :term do
      summary 'Add term to the glossary'
      notes 'Use this method in order to add a new term to the glossary'
      param :query, :data, :string, :required, 'JSON string that represents the term'
      authed = { 'Authorization' => 'Token token="test"' }
      response :ok, 'Term was added successfully', { query: { data: TERM }, headers: authed }
      response 400, 'Missing parameters', { query: { }, headers: authed }
      response 401, 'Access denied', { query: { data: TERM } }
    end
    
    swagger_api :terms do
      summary 'Get terms from a post'
      notes 'Use this method in order to get terms from glossary'
      param :query, :data, :string, :required, 'JSON string that represents the input text'
      authed = { 'Authorization' => 'Token token="test"' }
      response :ok, 'Terms from the glossary for the given input', { query: { data: TERM_QUERY }, headers: authed }
      response 400, 'Missing parameters', { query: { }, headers: authed }
      response 401, 'Access denied', { query: { data: TERM_QUERY } }
    end

    swagger_api :delete do
      summary 'Delete term from the glossary'
      notes 'Use this method in order to delete a term from the glossary'
      param :query, :id, :string, :required, 'The term ID as assigned by ElasticSearch'
      authed = { 'Authorization' => 'Token token="test"' }
      response :ok, 'Terms from the glossary for the given input', { query: { id: TERM_ID }, headers: authed }
      response 400, 'Missing parameters', { query: { }, headers: authed }
      response 401, 'Access denied', { query: { id: TERM_ID } }
    end
  end
end
# :nocov:
