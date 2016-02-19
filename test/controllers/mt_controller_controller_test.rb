#encoding: utf-8
require File.join(File.expand_path(File.dirname(__FILE__)), '..', 'test_helper')

class MtControllerControllerTest < ActionController::TestCase
  def setup
    super
    @controller = Api::V1::MtController.new
  end
end
