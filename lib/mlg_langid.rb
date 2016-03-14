module Mlg
  class LangId
    @@langid = nil

    def start
      RubyPython.stop
      RubyPython.start
      s = RubyPython.import 'sys'
      s.path.insert(0, CONFIG['langid']).rubify
      langid = RubyPython.import 'langid'
      @@langid = langid.LangId.new(MODEL_SENTENCES,LANGUAGES,STOPWORDS_PATH)


      #@@langid.trainPRELOAD(CONFIG['langid'] + '/dysl/corpora/multiLanguage/trainedCorpus2.obj').rubify
    end

    def try_to_classify(text)
      begin
        self.classify(text)
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
      @@langid.listLanguages.rubify
    end

    protected

    def classify(text)
      @@langid.classify(text).rubify
    end
  end
end
