#encoding: utf-8 
# :nocov:
module TMDoc
  extend ActiveSupport::Concern

  # Not used right now
  # included do
  #   swagger_controller :TM, 'TM'

  #   swagger_api :tuple do
  #     summary 'POST: Add tuple in Translation Memory (TM); GET: Search TM'
  #     notes 'Use this method in order to add tuple in Translation Memory (TM)'
  #     param :query, :data, :string, :required, 'POST: {"l1":"english", "c1":"en","sentence1":"hello world", "l2":"portuguese", "c2":"pt", "sentence2":"oi mundo", "source":"test site", "time-zone": "PDT / MST"} ; GET: {"l1":"english", "c1":"en","sentence1":"hello world", context:{ "source":"test site", "time-zone": "PDT / MST"}}'
  #     response :ok, 'POST: Success; GET: { "type": "tupleTM", {"data": "[{"l2":"portuguese", "c2":"pt", "sentence2":"oi mundo"}]","context":{ "source":"test site", "time-zone": "PDT / MST"}}'
  #     response 400, 'Parameters missing (text was not provided)'
  #     response 401, 'Access denied'
  #   end

  #   swagger_api :language do
  #     summary 'Get languages in TM'
  #     notes 'Use this method in order to get languages in TM'
  #     response :ok, 'Returns list: { "type": "languages", "data": [["english","en"],["portuguese","pt"],["spanish","es"],["arabic","ar"]]}'
  #     response 400, 'Parameters missing (text was not provided)'
  #     response 401, 'Access denied'
  #   end

  #   swagger_api :source do
  #     summary 'Get sources in TM'
  #     notes 'Use this method in order to get sources in TM'
  #     response :ok, 'Returns list: { "type": "sources", "data": [["testSite.url", "Test Site"],["https://en.wiktionary.org/wiki/hello", "Greetings"]]}'
  #     response 400, 'Parameters missing (text was not provided)'
  #     response 401, 'Access denied'
  #   end

  # end
end
# :nocov:
