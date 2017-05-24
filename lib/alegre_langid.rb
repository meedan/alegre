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
      instance = langid.LangId.new(CONFIG['langid'])
      self.instantiate_langid(instance)
    end

    def classify(text)
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

    def delete_sample(str, lang)
      @@langid.delete_sample(str, lang).rubify
    end

    def list_languages
      @@langid.list_languages.rubify
    end

    # @expose
    def normalize(text,space_parameter=' ')
      require 'diacritics'
      String.send(:include, Diacritics::String)
      return text.permanent(space_parameter)
    end

    protected

    def classify!(text)
      errbit_url = ''
      errbit_key = ''
      begin
        errbit_url = 'http://' + Airbrake.configuration.host + ':' + Airbrake.configuration.port.to_s
        errbit_key = Airbrake.configuration.api_key
      rescue
      end
      @@langid.respond_to?(:try_to_classify) ? @@langid.try_to_classify(text, errbit_url, errbit_key).rubify : []
    end

    def instantiate_langid(value)
      @@langid = value
    end
  end
end
