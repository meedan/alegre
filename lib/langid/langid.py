# coding=UTF-8
from gensim import corpora, models, similarities
import re
import os
from detGensim import detGensim as detLanguage
import sys  
import hanzidentifier
import pickle

class LangId:  

	def add_sample(self, sentence, lang):
		try:
			idx = self.languages.index(lang)
			self.documents[idx] = self.documents[idx]  + self.threeGrams(self.normalize(unicode(sentence)))
			self.newModelFiles()
			return True	    
		except ValueError:
			return False

	def list_languages(self):
		return self.languages
      
	def __init__(self,trainPath,languages,stopwords_path):
		self.languages = languages #['ar', 'en', 'fa', 'hi', 'it', 'pt', 'tl', 'az', 'es', 'fr', 'id', 'ka', 'ru', 'tr']
		self.stopwords_path = stopwords_path
		#self.trainPath = trainPath
		if trainPath.endswith('/'):
			trainPath = trainPath[:-1]
		self.detLanguage = detLanguage(stopwords_path)
		self.trainPath = trainPath
		self.initVars()

#NOMES CONFIGURAVEIS
	def initVars(self):
		reload(sys)  
		sys.setdefaultencoding('utf8')

	    #print doc
		print self.trainPath+'/corpus.mm',os.path.exists(self.trainPath+'/corpus.mm'),os.path.exists(self.trainPath)
		if os.path.exists(self.trainPath+'/corpus.mm'):
			self.dictionary = corpora.Dictionary.load(self.trainPath+'/dict.dict')
			self.corpus = corpora.MmCorpus(self.trainPath+'/corpus.mm')
			self.tfidf = models.TfidfModel.load(self.trainPath+'/model.tfidf')
			self.documents = pickle.load( open(self.trainPath+'/documents.obj', "rb" ) )
		else:
			self.documents = []

			for lang in self.languages:
				self.documents.append(self.readFile(self.trainPath+'/'+lang.lower()))
			self.newModelFiles()

	def newModelFiles(self):

		self.texts = []

		for document in self.documents:
		    self.texts.append(document.lower().split())   	    

		self.dictionary = corpora.Dictionary(self.texts)
		self.corpus = [self.dictionary.doc2bow(text) for text in self.texts]
		self.dictionary.save(self.trainPath+'/dict.dict')
		corpora.MmCorpus.serialize(self.trainPath+'/corpus.mm', self.corpus)
		self.tfidf = models.TfidfModel(self.corpus) # step 1 -- initialize a model
		self.tfidf.save(self.trainPath+'/model.tfidf') # same for tfidf, lda, ...
		pickle.dump(self.documents, open(self.trainPath+'/documents.obj', "wb" ) )

	def sim_tfidf(self, doc):
	    #print doc
	    try:
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
		if len(term) > 0:
		    if len(term) == 1:
		        ret = ret + term + ' '
		    else:
		        for i in range(len(term)-1):
		            ret = ret +  term[i:i+3] + ' '
	    return ret

	def normalize(self,text): 
	    """normalization for twitter"""
	    text = text.lower()
	    text = filter(lambda c: not c.isdigit(), text)
	    text = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text) #url
	    text = re.sub(r"(?:\@|\#)\S+", "", text) #@user #hashtag
	    text = re.sub(r'(^| )[:;x]-?[\(\)dop]($| )', ' ', text)  # facemark
	    text = re.sub(r'(^| )(rt[ :]+)*', ' ', text)
	    text = re.sub(r'([hj])+([aieo])+(\1+\2+){1,}', r'\1\2\1\2', text, re.IGNORECASE)  # laugh
	    text = re.sub(r' +(via|live on) *$', '', text)

	    # Match Emoticons
  	    myre = re.compile(u'['
	         u'\U0001F300-\U0001F64F'
	         u'\U0001F680-\U0001F6FF'
	         u'\u2600-\u26FF\u2700-\u27BF]+', 
	         re.UNICODE)

	    text = myre.sub('', text)
	    text = re.sub('«»“”"[.,!%@#$<>:;}?{()+-=-_&*@|\/"]+', '', text)
	    text = re.sub('(\!|#|\*|\?|,|;|:|%|\$|\"|\.\.\.)', '', text)

	    text = re.sub('\t', ' ', text)
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
		    fd.close()
          return i	


        def classify(self,line):
	   text = self.normalize(unicode(line))
	   ret = []
	   if hanzidentifier.has_chinese(text): #chinese
		#Chinese
		chineseArray = re.findall(ur'[\u4e00-\u9fff]+',text)
		chineseChars = len(str(chineseArray)) - (2+len(chineseArray))

		if len(text) / 3 < chineseChars: #At least 1/3 of the sentence in Chinese characteres
			if hanzidentifier.identify(text) is hanzidentifier.SIMPLIFIED:
				ret = [[1,'zh-CHS']]
			elif hanzidentifier.identify(text) is hanzidentifier.TRADITIONAL:
				ret = [[1,'zh-CHT']]
			elif hanzidentifier.identify(text) is hanzidentifier.BOTH:
				ret = [[1,'zh-CHT'],[1,'zh-CHS']]

		
	   #not chinese		
	   if len(ret) == 0:
			sims = self.sim_tfidf(self.threeGrams(text))
			if len(sims) > 0:
				language = ''

				lang1= self.languages[sims[0][0]].lower()
				lang2= self.languages[sims[1][0]].lower()
				if sims[0][1] > 0.004:
					language = self.languages[sims[0][0]]				
				else:
					language = 'unk'
					sims = []
				
		    		if ((lang1 == 'id')  and  (lang2 == 'tr') ): 		
					if text.find('ş') > -1:
					    language = 'tr'
		    		if ((lang1 == 'tr')  and  (lang2 == 'az') ): 		
					if text.find('ə') > -1:
					    language = 'az'
		    		elif ((lang1 == 'fr')  and  (lang2 == 'en') ) or ((lang1 == 'id')  and  (lang2 == 'en')) or ((lang1 == 'it')  and  (lang2 == 'en')) or ((lang1 == 'fa')  and  (lang2 == 'ar') ):
					lang = self.detLanguage.detect_language(text)
					if len(lang) > 0:
						language = lang
						ret.append ([1, str(lang.upper())])
				for s in sims:
					ret.append( [ str(s[1]), str(self.languages[s[0]])])
	   return ret

if __name__ == '__main__':
	#l = LangId('/home/ccx/work/alegre/lib/langid/modelSentences/',['AR', 'EN', 'FA', 'HI', 'IT', 'PT', 'TL', 'AZ', 'ES', 'FR', 'ID', 'KA', 'RU', 'TR','zh-CHT','zh-CHS'],'/home/ccx/work/alegre/lib/langid/stopwords/')
	#print '-',l.classify('“Please watch your inbox for important information about your employment status tomorrow.” : http://jimromenesko.com/2015/11/03/layoffs-begin-at-national-geographic/ …')
	#print '->>',l.add_sample('um dois três','PT')
	#print '->>',l.add_sample('um dois três','PTsdsdsds')
