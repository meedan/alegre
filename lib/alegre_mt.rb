module Alegre
  class Mt
    def initialize
      @mt = BingTranslator.new(CONFIG['bing_cognitive_subscription_key'])
    end

    def languages
      Rails.cache.fetch('supported_languages_for_mt', expires_in: 24.hours) do
        @mt.supported_language_codes.map(&:downcase)
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
