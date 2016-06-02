module Alegre
  class LangId
    @@langid = nil

    def start
      RubyPython.stop
      sleep 1
      RubyPython.start
      s = RubyPython.import 'sys'
      s.path.insert(0, File.join(Rails.root, 'lib/langid')).rubify
      langid = RubyPython.import 'langid'
      instance = langid.LangId.new
      self.instantiate_langid(instance)
    end

    def classify(text)
      text = self.normalize(text)
      begin
        self.classify!(text)
      rescue Exception => e
        Rails.logger.info "AlegreLangIdLib: An error of type #{e.class} happened, message is: #{e.message}"
        self.start
        self.classify!(text)
      end
    end

    def add_sample(str, lang)
      @@langid.add_sample(str, lang).rubify
    end

    def list_languages
      @@langid.list_languages.rubify
    end

    # TODO
    # @expose
    def normalize(text)
      text
    end

    protected

    def classify!(text)
      @@langid.respond_to?(:classify) ? @@langid.classify(text).rubify : []
    end

    def instantiate_langid(value)
      @@langid = value
    end
  end
end
