# coding=UTF-8
from gensim import corpora, models, similarities
import re
import os
from detGensim import detGensim as detLanguage
import sys  

class LangDetect:        
	def initVars(self,documents):
	    #print doc
	    if os.path.exists('./corpusTest2.mm'):
		    self.dictionary = corpora.Dictionary.load('./dictTest2.dict')
		    self.corpus = corpora.MmCorpus('./corpusTest2.mm')
		    self.tfidf = models.TfidfModel.load('./model2.tfidf')

	    else:

		    self.texts = []

		    for document in documents:
			    self.texts.append(document.lower().split())   	    

		    self.dictionary = corpora.Dictionary(self.texts)
		    self.corpus = [self.dictionary.doc2bow(text) for text in self.texts]
  		    self.dictionary.save('./dictTest2.dict')
		    corpora.MmCorpus.serialize('./corpusTest2.mm', self.corpus)
    		    self.tfidf = models.TfidfModel(self.corpus) # step 1 -- initialize a model
		    self.tfidf.save('./model2.tfidf') # same for tfidf, lda, ...


	def sim_tfidf(self,documents, doc):
	    #print doc
	    try:
		    print 'TFIDF'
		    vec_bow = self.dictionary.doc2bow(doc.lower().split())
		    vec_tfidf = self.tfidf[vec_bow] # convert the query to LSI space

		    index = similarities.MatrixSimilarity(self.tfidf[self.corpus])
		    sims = index[vec_tfidf]
		    return sorted(enumerate(sims), key=lambda item: -item[1])
 	    except ValueError:
		    return []



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
	    
	    text = re.sub('“”"[.,!%@#$<>:;}?{()+-=-_&*@|\/"]+', '', text)
	    text = re.sub('\n', '', text)
	    text = re.sub('\[', '', text)
	    text = re.sub('\]', '', text)

	    return text


	def readFile(self,filesPath):
	  i = u''
	  for file in os.listdir(filesPath):
	    if file.endswith(".txt"):

		    fd = open(filesPath+'/'+file, 'r')
		    for line in fd.readlines():
			try:
			    s = self.threeGrams(self.normalize(unicode(line)))
			    i = i+s
			except ValueError:
			    i = i
			    #print "Oops!",line,folder
		
		    fd.close()
          return i	


###

reload(sys)  
sys.setdefaultencoding('utf8')

l = LangDetect()
languages = ['ar', 'en', 'fa', 'hi', 'it', 'pt', 'tl', 'az', 'es', 'fr', 'id', 'ka', 'ru', 'tr']
documents = []
trainPath = '/home/ccx/work/alegre/lib/langid/dysl/etc/'
for lang in languages:
	documents.append(l.readFile(trainPath+lang))

wf = open('./rl2.txt', 'w')


filesPath = '/home/ccx/work/alegre/lib/langid/dysl/testSentences/' # './lSent/'
l.initVars(documents)
finalP_tfidf = []
finalP_lsi= []
for file in os.listdir(filesPath):
    if file.endswith(".txt"):
	currentLang = file.replace(".txt","")
	fd = open(filesPath+'/'+file, 'r')
	print "-->",file
	wf.write( "-->"+file)
	precision_lsi = 0
	precision_tfidf = 0
	nLines = 0
	for line in fd.readlines():
		if len(line.replace(' ','')) > 1:  
			result = currentLang+'\t'
			text = l.normalize(unicode(line))


			### sim_tfidf(self,documents, doc):
			sims = l.sim_tfidf(documents, l.threeGrams(text))
			aux = ''
			language = ''
			for  s in sims:
				aux = aux + '['+str(languages[s[0]])+' , '+str(s[1])+']'
			dif = sims[0][1]-sims[1][1]
			'''
			if dif < 0.1:
				det = detLanguage('/home/ccx/work/dysl/dysl/corpora/stopwords')
				language = det.detect_language(text)
    			'''
			result = result + 'tfidf'+'\t'+str(aux)+'\t'+str(text)+'\t'+str(line)
			print  result
			wf.write(result)

			if len(sims) > 0:
				if languages[sims[0][0]] == currentLang:
					precision_tfidf = precision_tfidf + 1

			nLines = nLines + 1
			print 'SIMS',str(currentLang),'tfidf->',precision_tfidf,'nLines',nLines

	precisionFinal_tfidf = float(precision_tfidf) / float(nLines)
	finalP_tfidf.append ( [currentLang,precisionFinal_tfidf] )
	print str(currentLang),'tfidf->',precisionFinal_tfidf#,'lsi->',precisionFinal_lsi
	wf.write(str(currentLang)+' tfidf->'+str(precisionFinal_tfidf)+'\n')#+' lsi->'+str(precisionFinal_lsi)
	fd.close
n = 0
while n < len(languages):
	print 'tfidf->',finalP_tfidf[n]#,'lsi->',finalP_lsi[n]
	wf.write('tfidf-> '+str(finalP_tfidf[n])+'\n')#+', lsi-> ' +str(finalP_lsi[n])
	n = n + 1

wf.close()
