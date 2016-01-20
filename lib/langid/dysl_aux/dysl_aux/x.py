#coding:utf-8
import gensim

def threeGrams(b):
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


documents = [threeGrams("Human machine interface for lab abc computer applications"),
             threeGrams("A survey of user opinion of computer system response time"),
             threeGrams("The EPS user interface management system"),
             threeGrams("System and human system engineering testing of EPS"),
             threeGrams("Relation of user perceived response time to error measurement"),
             threeGrams("The generation of random binary unordered trees"),
             threeGrams("The intersection graph of paths in trees"),
             threeGrams("Graph minors IV Widths of trees and well quasi ordering"),
             threeGrams("Graph minors A survey")]

texts = []
# remove common words and tokenize
for document in documents:
	for document in documents:
		texts.append(document.lower().split())
#print texts
dictionary = gensim.corpora.Dictionary(texts)
#dictionary.save('deerwester.dict') # store the dictionary, for future reference

#print(dictionary.token2id)

new_docs = [threeGrams("Human computer interaction")]
new_doc = threeGrams("Human computer interaction")
new_text = new_doc.lower().split()

new_vec = dictionary.doc2bow(new_doc.lower().split())
#print(new_vec)



corpus = [dictionary.doc2bow(text) for text in texts]
#gensim.corpora.MmCorpus.serialize('/tmp/deerwester.mm', corpus) # store to disk, for later use
#print(corpus)
#print threeGrams(u'uma sentença teste')

model = gensim.models.Word2Vec(texts)
word = 'hum'
if word in model.vocab:
	print model[word]
#print model['gra']

from scipy import spatial

dataSetI = [3, 45, 7, 2]
dataSetII = [2, 54, 13, 15]
result = 1 - spatial.distance.cosine(dataSetI, dataSetII)



