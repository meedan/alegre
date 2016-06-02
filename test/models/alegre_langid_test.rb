require File.join(File.expand_path(File.dirname(__FILE__)), '..', 'test_helper')

class AlegreLangidTest < ActiveSupport::TestCase
  test "should not crash if input is bad" do
    assert_nothing_raised do
      Alegre::LangId.new.classify(nil)
    end
  end

  test "should not crash if self is bad" do
    assert_nothing_raised do
      Alegre::LangId.new.send(:instantiate_langid, nil)
      Alegre::LangId.new.classify('test')
    end
    Alegre::LangId.new.start
  end
end
