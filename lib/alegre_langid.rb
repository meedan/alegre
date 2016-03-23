module Alegre
  class LangId
    @@langid = nil

    def start
      RubyPython.stop
      RubyPython.start
      s = RubyPython.import 'sys'
      s.path.insert(0, '/home/ccx/work/alegre/lib/langid').rubify
      langid = RubyPython.import 'langid'
      @@langid = langid.LangId.new()
    end

    def classify(text)
      begin
        @@langid.classify(text).rubify
      rescue Exception => e
        Rails.logger.info "AlegreLangIdLib: An error of type #{e.class} happened, message is: #{e.message}"
        self.start
        self.classify(text)
      end
    end

    def add_sample(str, lang)
      @@langid.add_sample(str, lang).rubify
    end

    def list_languages
      @@langid.list_languages.rubify
    end
  end
end
