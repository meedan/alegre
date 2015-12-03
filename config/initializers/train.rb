require 'rubypython'

MODEL_FILE = CONFIG['dysl'] + '/dysl/corpora/multiLanguage/trainedCorpus2.obj'
STOPWORDS_PATH = CONFIG['dysl'] + '/dysl/corpora/stopwords'

RubyPython.stop
RubyPython.start
s = RubyPython.import 'sys'
s.path.insert(0, CONFIG['dysl']).rubify
dysl = RubyPython.import 'dysl.langid'
DYSL = dysl.LangID.new
DYSL.trainPRELOAD(CONFIG['dysl'] + '/dysl/corpora/multiLanguage/trainedCorpus2.obj').rubify
