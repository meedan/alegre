# :nocov:
module LanguagesDoc
  extend ActiveSupport::Concern
 
  included do
    swagger_controller :languages, 'Languages'

    swagger_api :classify do
      summary 'MLG - Send some text to be classified'
      notes 'MLG - Use this method in order to identify the language of a given text'
      param :query, :text, :string, :required, 'Text to be classified'
      response :ok, 'Returns text language'
      response 400, 'Parameters missing (text was not provided)'
      response 401, 'Access denied'
    end
  end
end
# :nocov:
