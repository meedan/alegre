#encoding: utf-8
require File.join(File.expand_path(File.dirname(__FILE__)), '..', 'test_helper')

class GlossaryControllerTest < ActionController::TestCase

  def setup
    super
    @controller = Api::V1::GlossaryController.new
  end


  test "should add single word term to dictionary" do
    sleep(0.5)
    authenticate_with_token
    post :term, data: '{"lang": "en", "definition": "test definition","term": "test3","translations": [ {"lang": "pt","definition": "definição de teste","term": "teste"}],"context": { "source": {"url": "testSite.url","name": "test site"},"post": "xxxx","data_source": "dictionary","time-zone": "PDT / MST"} }'
    assert_response 200
  end

  test "should get single word term to dictionary" do
    sleep(0.5)
    authenticate_with_token
    get :terms, data: '{"lang": "en", "term": "test3"}'
    assert_response 200
  end

  test "should delete single word term from dictionary" do
    sleep(1)
    authenticate_with_token
    get :terms, data: '{"lang": "en", "term": "test3"}'
    str = assigns(:glossary)[0]
    str =  str.gsub! '=>', ':'
    data_hash = JSON.parse(str)
    post :delete, id: data_hash["_id"]
    assert_response 200
  end

  test "should add single Arabic word term to dictionary" do
    sleep(0.5)
    authenticate_with_token
    post :term, data: '{"lang": "ar", "definition": "test definition","term": "حكمة","translations": [ {"lang": "en","definition": "definição de teste","term": "teste"}],"context": { "source": {"url": "testSite.url","name": "test site"},"post": "xxxx","data_source": "dictionary","time-zone": "PDT / MST"} }'
    assert_response 200
  end

  test "should get single word term to dictionary from Arabic sentence" do
    sleep(0.5)
    authenticate_with_token
    get :terms, data: '{"lang": "ar", "term": "حكمة عظيمة"}'
    assert_response 200
  end

  test "should delete single Arabic word term from dictionary" do
    sleep(2)
    authenticate_with_token
    get :terms, data: '{"lang": "ar", "term":  "حكمة"}'
    str = assigns(:glossary)[0]
    str =  str.gsub! '=>', ':'
    data_hash = JSON.parse(str)

    post :delete, id: data_hash["_id"]
    assert_response 200
  end

  test "should add single Portuguese word term to dictionary" do
    sleep(0.5)
    authenticate_with_token
    post :term, data: '{"lang": "pt", "definition": "test definition","term": "Teste","translations": [ {"lang": "en","definition": "definição de teste","term": "teste"}],"context": { "source": {"url": "testSite.url","name": "test site"},"post": "xxxx","data_source": "dictionary","time-zone": "PDT / MST"} }'
    assert_response 200
  end

  test "should get single word term to dictionary from Portuguese sentence" do
    sleep(0.5)
    authenticate_with_token
    get :terms, data: '{"lang": "pt", "term": "Eu estou testando"}'
    assert_response 200
  end

  test "should delete single Portuguese word term from dictionary" do
    sleep(1)
    authenticate_with_token
    get :terms, data: '{"lang": "pt", "term":  "teste"}'
    str = assigns(:glossary)[0]
    str =  str.gsub! '=>', ':'
    data_hash = JSON.parse(str)

    post :delete, id: data_hash["_id"]
    assert_response 200
  end

  test "should not create term if term is missing" do
    sleep(0.5)
    authenticate_with_token
    post :term, data: '{"lang": "pt", "definition": "test definition","translations": [ {"lang": "en","definition": "definição de teste","term": "teste"}],"context": { "source": {"url": "testSite.url","name": "test site"},"post": "xxxx","data_source": "dictionary","time-zone": "PDT / MST"} }'
    assert_response 400
  end

  test "should not create term if lang is missing" do
    sleep(0.5)
    authenticate_with_token
    post :term, data: '{ "term":"teste", "definition": "test definition","translations": [ {"lang": "en","definition": "definição de teste","term": "teste"}],"context": { "source": {"url": "testSite.url","name": "test site"},"post": "xxxx","data_source": "dictionary","time-zone": "PDT / MST"} }'
    assert_response 400
  end

  test "should not create duplicated term" do
    sleep(0.5)
    authenticate_with_token
    post :term, data: '{"lang": "pt", "term":"teste", "definition": "test definition","translations": [ {"lang": "en","definition": "definição de teste","term": "teste"}],"context": { "source": {"url": "testSite.url","name": "test site"},"post": "xxxx","data_source": "dictionary","time-zone": "PDT / MST"} }'
    sleep 1
    post :term, data: '{"lang": "pt", "term":"teste", "definition": "test definition","translations": [ {"lang": "en","definition": "definição de teste","term": "teste"}],"context": { "source": {"url": "testSite.url","name": "test site"},"post": "xxxx","data_source": "dictionary","time-zone": "PDT / MST"} }'
    assert_response 400

    get :terms, data: '{"lang": "pt", "term":  "teste"}'
    str = assigns(:glossary)[0]
    str =  str.gsub! '=>', ':'
    data_hash = JSON.parse(str)
    post :delete, id: data_hash["_id"]

  end

  test "term - should return error if data was not provided" do
    authenticate_with_token
    post :term
    assert_response 400
  end

  test "term - should return error if data is empty" do
    authenticate_with_token
    post :term, data:''
    assert_response 400
  end

  test "term - should return error if invalid json" do
    authenticate_with_token
    post :term, data:'{lang:en, term:empty}'
    assert_response 400
  end

  test "terms - should return error if data was not provided" do
    authenticate_with_token
    get :terms
    assert_response 400
  end

  test "terms - should return error if data is empty" do
    authenticate_with_token
    get :terms, data:''
    assert_response 400
  end

  test "terms - should return error if invalid json" do
    authenticate_with_token
    get :terms, data:'{lang:en, term:empty}'
    assert_response 400
  end

  test "delete - should return error if invalid id" do
    authenticate_with_token
    post :term, id:'00000000'
    assert_response 400
  end

  test "delete - should return error if data is empty" do
    authenticate_with_token
    post :delete, data:''
    assert_response 400
  end

  test "delete - should return error if data was not provided" do
    authenticate_with_token
    post :delete
    assert_response 400
  end

end


