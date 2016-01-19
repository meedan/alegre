#encoding: utf-8 
# :nocov:
module DictionaryDoc
  extend ActiveSupport::Concern
 
  included do
    swagger_controller :dictionary, 'Dictionary'

 #### Insert term in Dictionary
    swagger_api :execute do
      summary 'Search terms in babelfy and insert it in dictionary'
      notes 'Use this method in order to search terms in babelfy and insert it in dictionary'
      param :query, :language, :string, :required, 'Language'
      param :query, :text, :string, :required, 'Text to be searched'
      param :query, :postid, :string, :optional, 'Post id'
      authed = { 'Authorization' => 'Token token="test"' }
      response :ok, 'Success'
      response 400, 'Error'
      response 401, 'Access denied'
    end

  end
end
# :nocov:
