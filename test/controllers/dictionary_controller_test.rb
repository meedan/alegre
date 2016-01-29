#encoding: utf-8
require File.join(File.expand_path(File.dirname(__FILE__)), '..', 'test_helper')
require 'retriable'


class DictionaryControllerTest < ActionController::TestCase
  def setup
    super
    @controller = Api::V1::DictionaryController.new
  end

  test "dict - should return error if text blank" do
    authenticate_with_token
    get :terms, language: 'en', text: '', source_id: '123456'
    assert_response 400
  end

  test "dict - should return error if language blank" do
    authenticate_with_token
    get :terms, language: '', text: 'one example', source_id: '123456'
    assert_response 400
  end

  test "dict - should return error if language does not exist" do
    authenticate_with_token
    get :terms, language: 'XXXXXXXXXXXXXXXXXX', text: 'one example', source_id: '123456'
    assert_response 400
  end

  test "dict - should return error parameters blank" do
    authenticate_with_token
    get :terms, language: '', text: '', source_id: '123456'
    assert_response 400
  end

  test "dict - should return sucess with 2 parameters" do
    authenticate_with_token
    get :terms, language: 'en', text: 'The book is on the table', source_id: '123456'
    assert_response :success
    assert_equal ['book', 'table'], JSON.parse(@response.body)['data'].collect{ |t| t['_source']['term'].strip }.sort
    assert assigns(:babelfy_requested)
  end

  test "dict - should not request Babelfy if terms are there" do
    authenticate_with_token
    get :terms, language: 'en', text: 'The book is on the table', source_id: '123456'
    assert_response :success
    assert_equal ['book', 'table'], JSON.parse(@response.body)['data'].collect{ |t| t['_source']['term'].strip }.sort
    assert assigns(:babelfy_requested)

    get :terms, language: 'en', text: 'The book is on the table', source_id: '123456'
    assert_response :success
    assert_equal ['book', 'table'], JSON.parse(@response.body)['data'].collect{ |t| t['_source']['term'].strip }.sort
    assert !assigns(:babelfy_requested)
  end
end
