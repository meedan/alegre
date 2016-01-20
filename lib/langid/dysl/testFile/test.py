from dysl.langid import LangID

#python dysl.py --train  /home/ccx/work/dysl/dysl/corpora/test/testModel.obj --corpus /home/ccx/work/dysl/dysl/corpora/test
#Must run at /home/ccx/work/dysl

fd = open("./testFile/sentences.txt", 'r')
l = LangID(unk=False)
l.trainPRELOAD(filename="/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus2.obj")
for line in fd.readlines():
    lang = l.classify(line.decode('utf8'))
    print str(lang)+"\t"+ str(line)
