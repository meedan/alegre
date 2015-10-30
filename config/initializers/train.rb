require 'rubypython'

MODEL_FILE = "/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus2.obj"
STOPWORDS_PATH = "/home/ccx/work/dysl/dysl/corpora/stopwords"

RubyPython.stop
RubyPython.start
s = RubyPython.import "sys"
s.path.insert(0, '/home/ccx/work/dysl').rubify
dysl = RubyPython.import "dysl.langid"
DYSL = dysl.LangID.new
DYSL.trainPRELOAD("/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus2.obj").rubify
