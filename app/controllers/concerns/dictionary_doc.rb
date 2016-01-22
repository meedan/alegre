#encoding: utf-8 
# :nocov:
module DictionaryDoc
  extend ActiveSupport::Concern
 
  included do
    swagger_controller :dictionary, 'Dictionary'

    swagger_api :terms do
      summary 'Get dictionary terms (from Babelfy for the first time, then from ElasticSearch) for a text in a certain language'
      notes 'Get dictionary terms (from Babelfy for the first time, then from ElasticSearch) for a text in a certain language'
      param :query, :text, :string, :required, 'Text to be searched'
      param :query, :language, :string, :required, 'Source language of the text'
      authed = { 'Authorization' => 'Token token="test"' }
      response :ok, 'Terms from the dictionary', { query: { text: 'The book is on the table', lang: 'en' }, headers: authed }
      response 400, 'Missing parameters', { query: nil, headers: authed }
      response 400, 'Invalid language format', { query: { text: 'Test', lang: 'en_US' }, headers: authed }
      response 401, 'Access denied', { query: { text: 'Test', lang: 'en' } }
    end

  end
end
# :nocov:
