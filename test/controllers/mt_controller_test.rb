#encoding: utf-8
require File.join(File.expand_path(File.dirname(__FILE__)), '..', 'test_helper')

class MtControllerTest < ActionController::TestCase
  def setup
    super
    @controller = Api::V1::MtController.new
    authenticate_with_token
  end

  test "should get machine translation for a text" do
    get :index, text: 'The book is on the table', from: 'en', to: 'pt'
    assert_equal 'O livro está na mesa', parse_response
  end

  test "should not get machine translations if from is missing" do
    get :index, text: 'The book is on the table', to: 'pt'
    assert_response 400
  end

  test "should not get machine translations if to is missing" do
    get :index, text: 'The book is on the table', from: 'en'
    assert_response 400
  end

  test "should not get machine translations if text is missing" do
    get :index, from: 'en', to: 'pt'
    assert_response 400
  end

  test "should not get machine translations if from is not supported" do
    get :index, text: 'The book is on the table', from: 'xy', to: 'pt'
    assert_response 400
  end

  test "should not get machine translations if to is not supported" do
    get :index, text: 'The book is on the table', from: 'en', to: 'xy'
    assert_response 400
  end

  test "should get machine translations for Chinese" do
    get :index, text: '这是一个测试', from: 'zh-chs', to: 'en'
    assert_response :success
  end

  test "should get supported languages" do
    get :languages
    languages = parse_response
    assert_kind_of Array, languages
    assert languages.size > 1
  end

  private

  def parse_response
    JSON.parse(@response.body)['data']
  end
end
