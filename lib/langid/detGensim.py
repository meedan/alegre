#!/usr/bin/env python
#coding:utf-8
# Detecting language using a stopwords based approach with gensim

import os

try:
	from gensim import utils, matutils
	from gensim.models import word2vec
except ImportError:
    print '[!] You need to install gensim'


class detGensim:


	def decode_input(text_in):
	    """ Decodes `text_in`
		If text_in is is a string, 
		then decode it as utf-8 string.
		If text_in is is a list of strings,
		then decode each string of it, 
		then combine them into one outpust string.  
	    """
	    
	    if type(text_in) == list:
		text_out = u' '.join([t.decode('utf-8') for t in text_in])
	    else:
		text_out = text_in.decode('utf-8')
	    return text_out


	langIds = []
	vecs = {}
	model = {}
	def __init__(self, mypath):
		if mypath.endswith('/'):
			mypath = mypath[:-1]
		for filename in os.listdir(mypath):
			self.vecs[filename] = vec(mypath+"/"+str(filename))
			self.model[filename] = word2vec.Word2Vec(self.vecs[filename].ss, size=2, min_count=1)


    	@classmethod
	def detect_language(self,text):

		sim = []
		n = 0
		for item in self.model:
			#print item
			sim = similar(self.model[item],self.vecs[item],text)
			#print sim
			if (n == 0) or (n < sim):
				lang = item
				n = sim
	
		#print "return ",lang
		if (n == (len(text.lower().split()) * -1)):
			return ""
		else:
			return lang			


class vec:
    def __init__(self, fi):

	self.ss = []
	self.ss2=[]
	for line in open(fi):
		self.ss.append([line.replace("\n", "").lower()])
		self.ss2.append(line.replace("\n", "").lower())


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
	detGensim("/home/ccx/work/alegre/lib/langid/stopword/")
	print "-->",detGensim.detect_language("aaa xcxcxc")
	print "-->",detGensim.detect_language("sentence in english")
	print "-->",detGensim.detect_language("uma em que frase do portuguÊs")
	


