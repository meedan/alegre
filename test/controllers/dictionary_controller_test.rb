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
    post :execute, language: 'en', text: ''
    assert_response 400
  end

  test "dict - should return error if language blank" do
    authenticate_with_token
    post :execute, language: '', text: 'one example'
    assert_response 400
  end

  test "dict - should return error if language does not exist" do
    authenticate_with_token
    post :execute, language: 'XXXXXXXXXXXXXXXXXX', text: 'one example'
    assert_response 400
  end

  test "dict - should return error parameters blank" do
    authenticate_with_token
    post :execute, language: '', text: ''
    assert_response 400
  end


  test "dict - should return sucess with 2 parameters" do
    authenticate_with_token
    post :execute, language: 'en', text: 'This is a test '+Time.now.to_s
    assert_response :success
  end

  test "dict - should return sucess with 3 parameters" do
    authenticate_with_token
    post :execute, language: 'en', text: 'This is a test '+Time.now.to_s, postid: '0000'
    puts response.body
    assert_response :success
  end

end


