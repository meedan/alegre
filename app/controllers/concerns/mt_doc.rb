#encoding: utf-8 
# :nocov:
module MtDoc
  extend ActiveSupport::Concern
 
  included do
    swagger_controller :mt, 'Machine Translation'

    swagger_api :index do
      summary 'Machine-translate some text'
      notes 'Use this method in order to get a machine translation for a text, given source and target languages'
      param :query, :text, :string, :required, 'Original text'
      param :query, :from, :string, :required, 'Source language (two-letters code)'
      param :query, :to, :string, :required, 'Target languages (two-letters code)'
      authed = { CONFIG['authorization_header'] => 'test' }
      response :ok, 'Machine translation', { query: { text: 'This is a test', from: 'en', to: 'pt' }, headers: authed }
      response 400, 'Some parameter is missing', { query: { text: 'This is a test', to: 'pt' }, headers: authed }
      response 400, 'Language not supported', { query: { text: 'This is a test', from: 'xy', to: 'pt' }, headers: authed }
      response 401, 'Access denied', { query: { text: 'This is a test', from: 'en', to: 'pt' } }
    end

    swagger_api :languages do
      summary 'Get supported languages'
      notes 'Use this method in order to get a list of all languages supported for machine translation, in two-letters code'
      authed = { CONFIG['authorization_header'] => 'test' }
      response :ok, 'Supported languages', { headers: authed }
      response 401, 'Access denied', {}
    end
  end
end
# :nocov:
