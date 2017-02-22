#encoding: utf-8
require File.join(File.expand_path(File.dirname(__FILE__)), '..', 'test_helper')

class LanguagesControllerTest < ActionController::TestCase
  def setup
    super
    @controller = Api::V1::LanguagesController.new
  end

  test "identification - should get language en" do
    authenticate_with_token
    get :identification, text: 'This is a sentence in English'
    assert_response :success
    assert_equal "EN", assigns(:language)[0][0]   
  end

  test "identification - should get language es" do
    authenticate_with_token
    get :identification, text: 'Esta es una frase en español'
    assert_response :success
    assert_equal "ES", assigns(:language)[0][0]   
  end

  test "identification - should get language pt" do
    authenticate_with_token
    get :identification, text: 'Esta é uma frase em português'
    assert_response :success
    assert_equal "PT", assigns(:language)[0][0]   
  end

  test "identification - should get language ar" do
    authenticate_with_token
    get :identification, text: 'هذه هي العبارة باللغة العربية'
    assert_response :success
    assert_equal "AR", assigns(:language)[0][0]   
  end

  test "identification - should get language en+ar" do
    authenticate_with_token
    get :identification, text: 'in the morning evening at night غدا  البارحة غدا  البارحة'
    assert_response :success
    assert_equal "EN,AR", assigns(:language)[0][0]
  end
  
  test "identification - should return error empty if test is in a unknown language" do
    authenticate_with_token
    get :identification, text: 'x'
    assert_response :success
    assert_equal [], assigns(:language)
  end

  test "identification - should return error empty if test is in a unknown language - signs" do
    authenticate_with_token
    get :identification, text: '♥ →'
    assert_response :success
    assert_equal [], assigns(:language)
  end

  test "identification - should return english" do
    authenticate_with_token
    get :identification, text: 'I ♥ you English language'
    assert_response :success
    assert_equal "EN", assigns(:language)[0][0]   
  end

  test "identification - should not return english hashtag" do
    authenticate_with_token
    get :identification, text: '#English'
    assert_response :success
    assert_equal [], assigns(:language)
  end


  test "identification - should return error if text blank" do
    authenticate_with_token
    get :identification, text: ''
    assert_response 400
  end


  test "identification - should return error if text was not provided" do
    authenticate_with_token
    get :identification
    assert_response 400
  end

  test "sample - should return error if no parameter was not provided" do
    authenticate_with_token
    post :sample
    assert_response 400
  end

  test "sample - should return error if language was not provided" do
    authenticate_with_token
    post :sample, text: '#English'
    assert_response 400
  end

  test "sample - should return error if text was not provided" do
    authenticate_with_token
    post :sample, language: 'EN'
    assert_response 400
  end

  test "sample - should return sucess" do
    authenticate_with_token
    post :sample, language: 'EN', text: 'sample text in english language'
    assert_response :success
  end

  test "sample - should return error if text blank" do
    authenticate_with_token
    post :sample, language: 'EN', text: ''
    assert_response 400
  end

  test "sample - should return error if language blank" do
    authenticate_with_token
    post :sample, language: '', text: 'one example'
    assert_response 400
  end

  test "sample - should return error parameters blank" do
    authenticate_with_token
    get :sample, language: '', text: ''
    assert_response 400
  end


  test "language - should return list" do
    arrayVar = [1]
    authenticate_with_token
    get :language
    assert_response :success
    assert_equal arrayVar.class, assigns(:list).class
  end

  # http://mantis.meedan.net/view.php?id=4801
  test "language - should not crash with Python unary operand error" do
    authenticate_with_token
    texts = [
      '「ふるさと納税」商品券 大多喜町は廃止、勝浦市は継続: ふるさと納税」の特典競争が過熱する中、一万円寄付すると六千円分がもらえる商品券「ふるさと感謝券」を贈る特典を今月限りで廃止する大多喜町。換金性が ... https://t.co/ogqfRArQwY #Test',
      'https://t.co/dZJ58CWhjx #Jordan #ﺍﻷﺭﺪﻧ'
    ]
    texts.each do |text|
      assert_nothing_raised do
        get :identification, text: text
        assert_response :success
      end
    end
  end

  # https://mantis.meedan.com/view.php?id=4896
  test "0004896: Python exception on Bridge Live" do
    authenticate_with_token
    get :identification, text: 'CR7 মাঠ ছে‌ড়ে যাওয়ার পর খেলা বন্ধ কর‌ে ঘুমাই‌তে গে‌ছিলাম। সকা‌লে উ‌ঠে দে‌খি পর্তুগাল জি‌তে গে‌ছে!'
    assert_response :success
    assert_equal [], assigns(:language)
  end

  test "language - should not crash with function object error" do
    authenticate_with_token
    text = 'So devastated over this shooting at UCLA. Sending all my thoughts and prayers to the Bruins.'
    assert_nothing_raised do
      get :identification, text: text
      assert_response :success
    end
  end

  test "language - diacritic normalization" do
    authenticate_with_token
    get :normalize, text: 'ç ã Ñ'
    assert_response :success
    assert_equal 'c a n', assigns(:text)
  end

  test "language - diacritic normalization when text is not present" do
    authenticate_with_token
    get :normalize
    assert_response 400
  end
end
