# Elasticsearch helpers

def language_to_analyzer(lang):
  analyzer_dict = {
    'ar': 'arabic',
    'hy': 'armenian',
    'eu': 'basque',
    'bn': 'bengali',
    'pt-br': 'brazilian', # TODO
    'bg': 'bulgarian',
    'ca': 'catalan',
    'cjk': 'cjk', # TODO
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'fi': 'finnish',
    'fr': 'french',
    'gl': 'galician',
    'de': 'german',
    'gr': 'greek',
    'hi': 'hindi',
    'hu': 'hungarian',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'no': 'norwegian',
    'fa': 'persian',
    'pt': 'portuguese',
    'ro': 'romanian',
    'ru': 'russian',
    'ku': 'sorani',
    'es': 'spanish',
    'sv': 'swedish',
    'tr': 'turkish',
    'th': 'thai'
  }
  return analyzer_dict.get(lang, 'standard')
