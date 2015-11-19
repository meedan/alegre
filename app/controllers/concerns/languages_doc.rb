#encoding: utf-8 
# :nocov:
module LanguagesDoc
  extend ActiveSupport::Concern
 
  included do
    swagger_controller :languages, 'Languages'

    swagger_api :identification do
      summary 'Identify the language of a given text'
      notes 'Use this method in order to identify the language of a given text'
      param :query, :text, :string, :required, 'Text to be classified'
      authed = { 'Authorization' => 'Token token="test"' }
      response :ok, 'Text language', { query: { text: 'The book is on the table' }, headers: authed }
      response 400, 'Parameter "text" is missing', { query: nil, headers: authed }
      response 401, 'Access denied', { query: { text: 'Test' } }
    end

    swagger_api :sample do
      summary 'Add training sample to the model'
      notes 'Use this method in order to add training sample to the model'
      param :query, :language, :string, :required, 'Language'
      param :query, :text, :string, :required, 'Text to be inserted'
      response :ok, 'Returns ok'
      response 400, 'Parameters missing (text was not provided)'
      response 401, 'Access denied'
    end

    swagger_api :language do
      summary 'List supported languages'
      notes 'Use this method in order to list supported languages'
      response :ok, 'Returns list'
      response 400, 'Parameters missing (text was not provided)'
      response 401, 'Access denied'
    end

  end
end
# :nocov:
