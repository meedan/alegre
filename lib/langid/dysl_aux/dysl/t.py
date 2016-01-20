#!/usr/bin/env python
#coding:utf-8
# Detecting language using a stopwords based approach with gensim


import re
import ngram
import operator
from os import walk
from utils import decode_input
import gensim
import os
try:
	from gensim import utils, matutils
	from gensim.models import word2vec
except ImportError:
    print '[!] You need to install gensim'

class vec:
    def __init__(self, fi):

	self.ss = []
	self.ss2=[]
	for line in open(fi):
		self.ss.append([decode_input(line.replace("\n", "").lower())])
		self.ss2.append(decode_input(line.replace("\n", "").lower()))



class detGensim:
	langIds = []
	vecs = {}
	model = {}
	def __init__(self, mypath):
		filenames = next(walk(mypath))[2]
		for filename in filenames:
			#print filename
			self.vecs[filename] = vec(mypath+"/"+str(filename))
			#print 'self.vecs[filename]',self.vecs[filename]
			self.model[filename] = word2vec.Word2Vec(self.vecs[filename].ss, size=2, min_count=1)
			#print 'self.model[filename]',self.model[filename]

    	@classmethod
	def detect_language(self,text):

		sim = []
		n = 0
		for item in self.model:
			print 'item',item,self.model[item]
			sim = similar(self.model[item],self.vecs[item],text)
			print sim
			if (n == 0) or (n < sim):
				lang = item
				n = sim
	
		#print "return ",lang
		if (n == (len(text.lower().split()) * -1)):
			return "unk"
		else:
			return lang			


class vec:
    def __init__(self, fi):

	self.ss = []
	self.ss2=[]
	for line in open(fi):
		self.ss.append([decode_input(line.replace("\n", "").lower())])
		self.ss2.append(decode_input(line.replace("\n", "").lower()))


def similar(model,v,txt):
	doc_tokens = utils.any2utf8(txt.lower()).split()
	print 'doc_tokens',doc_tokens,v.ss2
	w = filter(lambda x: x in v.ss2, doc_tokens)
	dif = len(doc_tokens) - len(w)	
	#print len(doc_tokens) , len(w)	
	if len(w) > 0:
		return model.n_similarity(v.ss2, w) - dif
	else:
		return dif * -1

class MySentences(object):
     def __init__(self, dirname):
         self.dirname = dirname
 
     def __iter__(self):
         for fname in os.listdir(self.dirname):
             for line in open(os.path.join(self.dirname, fname)):
                 yield line.split()

def mySentences(dirname):
	 l = {}
         for fname1 in os.listdir(dirname):
		 #print "--",fname
		 for fname in os.listdir(dirname+'/'+fname1):
		 	 l[fname] = u''
			 for fname2 in os.listdir(dirname+'/'+fname1+'/'+fname):
				content = open(os.path.join(dirname+'/'+fname1+'/'+fname, fname2)).read() 
		     		l[fname] = l[fname] + u' ' + normalize(content)

	 return l

#return threegrans in a sentence
def threeGrams(b):
	ret = []
	for term in b.split(' '):
		#print t
		#term = t.decode('utf-8')
		if len(term) > 0:
			#print term,len(term)

			if len(term) == 1:
				ret.append(term)
			else:
				for i in range(len(term)-1):
					ret.append(term[i:i+3])
	return ret

def normalize(t): 
	"""normalization for twitter"""
	txt = u''
	if not(isinstance(t, unicode)):
		txt = t.decode('utf-8')
	else:
		txt = t
	
	txt = txt.lower()
	txt = " ".join([x for x in txt.split(" ") if not x.isdigit()])
	txt = re.sub(r'(@|#|https?:\/\/)[^ ]+', '', txt)
	txt = re.sub(r'(^| )[:;x]-?[\(\)dop]($| )', ' ', txt)  # facemark
	txt = re.sub(r'(^| )(rt[ :]+)*', ' ', txt)
	txt = re.sub(r'([hj])+([aieo])+(\1+\2+){1,}', r'\1\2\1\2', txt, re.IGNORECASE)  # laugh
	txt = re.sub(r' +(via|live on) *$', '', txt)
	txt = re.sub(r' +(via|live on) *$', '', txt)
	txt = txt.replace("<3", "")
	txt = txt.replace('[', "")
	txt = txt.replace(']', "")
	txt = txt.replace('(', "")
	txt = txt.replace(')', "")
	txt = txt.replace('.', " ")
	txt = txt.replace(',', " ")
	txt = txt.replace(':', " ")
	txt = txt.replace('"', "")
	txt = txt.replace('\n', " ")

	char_aux = '•'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '—'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '‘'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '😈'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '😊'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '😄'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '👍'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '😂'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '✈'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '✔'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '❤'
	txt = txt.replace(char_aux.decode(encoding='UTF-8'), "")
	txt = re.sub('[.,!@#$<>:;}?{()+-=-_&*@|\/"]+', '', txt)
	return txt

def _contents(items, laplace=True):
    # count occurrences of values
    counts = {}
    for item in items:
        counts[item] = counts.get(item,0) + 1.0
    # normalize
    for k in counts:
        if laplace:
            counts[k] += 1.0
            counts[k] /= (len(items)+len(counts))
        else:
            counts[k] /= len(items)
    return counts


def langId(sentence, l):
	inputString = threeGrams(sentence)

	ngransFile = {}
	ngransFile_1 = {}
	dist = {}
	term_count_n = {}
	corpus_count_n = {}
	term_count_n = {}
        joiner = u' '
	d = {}
        for lang in l:
		doc_id = lang
		dist[lang] = 0.0
		#print l,type(l)
		d[lang] = []
	        for ngram_ in inputString: #ng in inputString:
			if ngram_ in l[lang]:
				r = l[lang].count(ngram_)
				d[lang].append(r)
				dist[lang] += r
		
		dist[lang] = _contents(d[lang], laplace=True) #round(dist[lang]/len(l[lang]), 5)

	return sorted(dist.items(), key=operator.itemgetter(1), reverse=True)

def similar(model,v,txt):
	doc_tokens = txt.lower().split()
	w = filter(lambda x: x in v.ss2, doc_tokens)
	dif = len(doc_tokens) - len(w)	
	#print len(doc_tokens) , len(w)	
	if len(w) > 0:
		return model.n_similarity(v.ss2, w) - dif
	else:
		return dif * -1

def myVecs(dirname):
	v = {}
	for fname1 in os.listdir(dirname):
	  #print "--",fname
	  for fname in os.listdir(dirname+'/'+fname1):
	 	 l[fname] = u''
		 for fname2 in os.listdir(dirname+'/'+fname1+'/'+fname):
			v[fname] = vec(os.path.join(dirname+'/'+fname1+'/'+fname+'/'+fname2))
	return v

def similar(model,v,txt):
	doc_tokens = txt.lower().split()
	w = filter(lambda x: x in v.ss2, doc_tokens)
	dif = len(doc_tokens) - len(w)	
	#print len(doc_tokens) , len(w)	
	if len(w) > 0:
		return model.n_similarity(v.ss2, w) - dif
	else:
		return dif * -1

if __name__ == '__main__':
	vecs = {}
	l = mySentences("/home/ccx/work/dysl/dysl/corpora/multiLanguage")
	vecs = myVecs("/home/ccx/work/dysl/dysl/corpora/multiLanguage")

	LanguagesNgrams={}
	model= {}
	for lang in l:
		#print lang
		LanguagesNgrams[lang] = threeGrams(l[lang])
		model[lang] = gensim.word2vec.Word2Vec(vecs[lang].ss, size=2, min_count=1)  #.models.Word2Vec(LanguagesNgrams[lang] )
		# train word2vec on the two sentences

	
	f = ['/home/ccx/work/api-mlg/lib/tw/pt.txt'] #,'/home/ccx/work/api-mlg/lib/tw/ar.txt','/home/ccx/work/api-mlg/lib/tw/en.txt','/home/ccx/work/api-mlg/lib/tw/es.txt','/home/ccx/work/api-mlg/lib/tw/pt.txt']

	import io

	target = io.open("r.txt", 'w', encoding='utf8')

	for file in f:
		for line in open(file):
			sentence = threeGrams(line.replace('\n',''))
			for item in model:
				#print item
				sim = similar(model[item],vecs[item],line)
				print sim
				if (n == 0) or (n < sim):
					lang = item
					n = sim




			'''
			line = normalize(line.replace('\n',''))
			id = langId(line,LanguagesNgrams)
			
			print file.replace('/home/ccx/work/api-mlg/lib/tw/','').replace('.txt','')+'\t',str(id[0][0]).decode('utf-8')+'\t',str(id)+'\t',line
			out = unicode(file.replace('/home/ccx/work/api-mlg/lib/tw/','').replace('.txt',''))+'\t'+unicode(id[0][0])+'\t'+unicode(id)+'\t'+unicode(line)
			target.write(unicode(out))
			target.write(unicode("\n"))
			'''
	target.close()
	#print langId(inputString)
'''
	ngransFilePT = threeGrams(mySentences('/home/ccx/work/dysl/dysl/corpora/multiLanguage/country/pt'))
	ngransFileAR = threeGrams(mySentences('/home/ccx/work/dysl/dysl/corpora/multiLanguage/country/ar'))
	t = threeGrams('português')


	import ngram
	pt = ngram.NGram(ngransFilePT)
	ar = ngram.NGram(ngransFileAR)
	sPT = 0
        for ng in t:
		s = pt.search(ng)
		if len(s) > 0:
			sPT = sPT +  s[0][1]
	sAR = 0

        for ng in t:
		s = ar.search(ng)
		if len(s) > 0:
			sAR = sAR +  s[0][1]

	print sPT, sAR
	#print m
	#dictionary =  gensim.corpora.Dictionary(m)
	#print(dictionary)
	#print m, t
	model = gensim.models.Word2Vec()
	sentences = gensim.models.word2vec.LineSentence("/home/ccx/work/dysl/dysl/corpora/multiLanguage/country/pt/file2.txt")
	model.build_vocab(sentences)
	model.train(sentences)
	print model.similarity(m, t)
	#print model.most_similar(positive=['woman', 'king'], negative=['man'], topn=1)
	'''


