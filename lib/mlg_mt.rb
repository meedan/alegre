module Mlg
  class Mt
    def initialize
      @mt = BingTranslator.new(CONFIG['bing_id'], CONFIG['bing_secret'])
    end

    def languages
      Rails.cache.fetch('supported_languages_for_mt', expires_in: 24.hours) do
        @mt.supported_language_codes
      end
    end

    def translate(text, from, to)
      translation = ''
      Retriable.retriable do
        translation = @mt.translate(text, from: from, to: to)
      end
      translation
    end
  end
end
