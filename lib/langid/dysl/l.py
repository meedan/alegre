#!/usr/bin/env python
#coding:utf-8
# Detecting language using a stopwords based approach with gensim


import gensim

from gensim import corpora, models, similarities

def readFiles():
	documents = {}
	fs = ['/home/ccx/work/aux/dysl/dysl/corpora/multiLanguage/etc/pt/file2.txt' ,'/home/ccx/work/aux/dysl/dysl/corpora/multiLanguage/etc/en/file2.txt' ,'/home/ccx/work/aux/dysl/dysl/corpora/multiLanguage/etc/ar/file2.txt' ]
	
	for file in fs:
		name = file.replace('/home/ccx/work/aux/dysl/dysl/corpora/multiLanguage/etc/','')
		name = name.replace('/file2.txt','')
		documents[name] = []
		for line in open(file):
			sentence = threeGrams(line.replace('\n',''))		
			documents[name].append(threeGrams(sentence.lower()))
	return documents

def threeGrams(b):
	ret = ''
	for term in b.lower().split(' '):
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

def sim(doc):
	vec_bow = dictionary.doc2bow(doc.lower().split())
	vec_lsi = lsi[vec_bow] # convert the query to LSI space
	index = similarities.MatrixSimilarity(lsi[corpus]) 
	sims = index[vec_lsi] # perform a similarity query against the corpus
	return sims

'''
documents = [threeGrams("Human machine interface for lab abc computer applications"),
             threeGrams("A survey of user opinion of computer system response time"),
             threeGrams("The EPS user interface management system"),
             threeGrams("System and human system engineering testing of EPS"),
             threeGrams("Relation of user perceived response time to error measurement"),
             threeGrams("The generation of random binary unordered trees"),
             threeGrams("The intersection graph of paths in trees"),
             threeGrams("Graph minors IV Widths of trees and well quasi ordering"),
             threeGrams("english example"),
             threeGrams("Graph minors A survey")]
'''
documents = readFiles()
texts = {}
dictionary={}
corpus={}

# remove common words and tokenize
for key, value in documents.iteritems():
	texts[key] = []
	print documents[key],key
	texts[key].append(documents[key].split())

for key, value in texts.iteritems():
	dictionary[key] = gensim.corpora.Dictionary(value)
	corpus[key] = [dictionary[key].doc2bow(text) for text in texts[key]]
quit()
#print(corpus)
lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=2)

sims = sim(threeGrams("Human computer interaction"))
quit()
print(list(enumerate(sims))) # print (document_number, document_similarity) 2-tuples

sims = sim(threeGrams("sdsdsdsd sdsdssd"))
#print(list(enumerate(sims))) # print (document_number, document_similarity) 2-tuples
