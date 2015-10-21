require File.join(File.expand_path(File.dirname(__FILE__)), '..', 'test_helper')

class ApiKeyTest < ActiveSupport::TestCase
  test "should create API key" do
    assert_difference 'ApiKey.count' do
      create_api_key
    end
  end

  test "should generate expiration date" do
    Time.stubs(:now).returns(Time.parse('2015-01-01 09:00:00'))
    k = create_api_key
    assert_equal Time.parse('2015-01-31 09:00:00'), k.reload.expire_at
  end

  test "should generate access token" do
    k = create_api_key
    assert_kind_of String, k.reload.access_token
  end

  test "should generate random data" do
    assert_kind_of String, random_string
    assert_kind_of Integer, random_number
    assert_kind_of String, random_email
  end
end
