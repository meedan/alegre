# coding=UTF-8
from gensim import corpora, models, similarities
import re
#dictionary = corpora.Dictionary.load('/tmp/deerwester.dict')

class LangDetect:         
	def threeGrams(self,b):
	    ret = ''
	    for term in b.split(' '):
		#print t
		#term = t.decode('utf-8')
		if len(term) > 0:
		    #print term,len(term)

		    if len(term) == 1:
		        ret = ret + term + ' '
		    else:
		        for i in range(len(term)-1):
		            ret = ret +  term[i:i+3] + ' '
	    return ret

	def normalize(self,text): 
	    """normalization for twitter"""
	    text = text.lower()
	    text = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text) #url
	    text = re.sub(r"(?:\@|\#)\S+", "", text) #@user #hashtag

	    text = re.sub(r'(^| )[:;x]-?[\(\)dop]($| )', ' ', text)  # facemark
	    text = re.sub(r'(^| )(rt[ :]+)*', ' ', text)
	    text = re.sub(r'([hj])+([aieo])+(\1+\2+){1,}', r'\1\2\1\2', text, re.IGNORECASE)  # laugh
	    text = re.sub(r' +(via|live on) *$', '', text)

	    char_aux = '😈'
	    text = text.replace(char_aux.decode(encoding='UTF-8'), "")
	    char_aux = '😊'
	    text = text.replace(char_aux.decode(encoding='UTF-8'), "")
	    char_aux = '😄'
	    text = text.replace(char_aux.decode(encoding='UTF-8'), "")
	    char_aux = '👍'
	    text = text.replace(char_aux.decode(encoding='UTF-8'), "")
	    char_aux = '😂'
	    text = text.replace(char_aux.decode(encoding='UTF-8'), "")
	    char_aux = '✈'
	    text = text.replace(char_aux.decode(encoding='UTF-8'), "")
	    char_aux = '✔'
	    text = text.replace(char_aux.decode(encoding='UTF-8'), "")
	    char_aux = '❤'
	    text = text.replace(char_aux.decode(encoding='UTF-8'), "")

	    text = re.sub('[.,!@#$<>:;}?{()+-=-_&*@|\/"]+', '', text)
	    text = re.sub('\n', '', text)
	    text = re.sub('\[', '', text)
	    text = re.sub('\]', '', text)

	    return text


	def readFile(self,f):
	    fd = open(f, 'r')
	    i = u''
	    for line in fd.readlines():
		try:
		    s = self.threeGrams(self.normalize(unicode(line)))
		    i = i+s
		except ValueError:
		    i = i
		    #print "Oops!",line
		
	    fd.close()
	    return i


	def sim(self,documents, doc):
	    #print doc
	    texts = []
	    # remove common words and tokenize
	    #for d in documents:
	    for document in documents:
		    texts.append(document.lower().split())
		    
	    
	    dictionary = corpora.Dictionary(texts)
	    corpus = [dictionary.doc2bow(text) for text in texts]
	    
	    #corpora.MmCorpus.serialize('/tmp/corpusTest.mm', corpus)
	    #corpus = corpora.MmCorpus('/tmp/corpusTest.mm')
	    
	    
	    lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=2)
	    vec_bow = dictionary.doc2bow(doc.lower().split())
	    vec_lsi = lsi[vec_bow] # convert the query to LSI space
	    #print(vec_lsi)
	    
	    #    Initializing query structures
	    index = similarities.MatrixSimilarity(lsi[corpus]) # transform corpus to LSI space and index it
	    sims = index[vec_lsi]

	    return sorted(enumerate(sims), key=lambda item: -item[1])
	    #sims = sorted(enumerate(sims), key=lambda item: -item[1]) # perform a similarity query against the corpus
	    #print(list(enumerate(sims))) # print (document_number, document_similarity) 2-tuples
		    
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

l = LangDetect()

documents = [l.readFile('/home/ccx/work/dysl/dysl/corpora/multiLanguage/etc/en/file2.txt'),
             l.readFile('/home/ccx/work/dysl/dysl/corpora/multiLanguage/etc/pt/file2.txt')]


#print len(documents)
print 'EN'
fd = open("/home/ccx/work/dysl/testSentences/en.txt", 'r')
for line in fd.readlines():
	sims = l.sim(documents, l.threeGrams(l.normalize(unicode(line))))
	print sims,str(line)
fd.close

print 'PT'
fd = open("/home/ccx/work/dysl/testSentences/pt.txt", 'r')
for line in fd.readlines():
	sims = l.sim(documents, l.threeGrams(l.normalize(unicode(line))))
	print sims,str(line)
fd.close

sims = l.sim(documents, l.threeGrams(u'天。, 今天是星期六。, 今天是星期二。, 今天是星期三。, 今天很热。'))
print sims
