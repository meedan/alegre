# coding=UTF-8
from dysl.langid import LangID
from dysl.utils import decode_input

#python dysl.py --train  /home/ccx/work/dysl/dysl/corpora/test/testModel.obj --corpus /home/ccx/work/dysl/dysl/corpora/test
#Must run at /home/ccx/work/dysl

fd = open("./testFile/sentences.txt", 'r')
l = LangID(unk=False)
l.trainPRELOAD(filename="/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus2.obj")
for line in fd.readlines():
    #print decode_input(line)
    lang = l.classify(decode_input(line))
    print (str(lang)+"\t"+ str(line))
