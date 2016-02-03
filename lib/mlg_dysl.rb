module Mlg
  class Dysl
    @@dysl = nil

    def start
      RubyPython.stop
      RubyPython.start
      s = RubyPython.import 'sys'
      s.path.insert(0, CONFIG['dysl']).rubify
      dysl = RubyPython.import 'dysl.langid'
      @@dysl = dysl.LangID.new
      @@dysl.trainPRELOAD(CONFIG['dysl'] + '/dysl/corpora/multiLanguage/trainedCorpus2.obj').rubify
    end

    def try_to_classify(text)
      begin
        self.classify(text)
      rescue Exception => e
        Rails.logger.info "MlgDyslLib: An error of type #{e.class} happened, message is: #{e.message}"
        self.start
        self.classify(text)
      end
    end

    def add_sample(str, lang)
      @@dysl.add_sample(str, lang, MODEL_FILE).rubify
    end

    def list_languages
      @@dysl.listLanguages.rubify
    end

    protected

    def classify(text)
      @@dysl.classifyReturnAll(text, STOPWORDS_PATH).rubify
    end
  end
end
