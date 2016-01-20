# coding=UTF-8
""" Language Identification

    Author: Tarek Amr (@gr33ndata)
    Updates: Clarissa Xavier (clarissacastella)
"""
import pickle

import sys
import os
import codecs
import re
#from dyslib.lm import LM
from social import SocialLM as LM
from corpora.corpuslib import Train
from utils import decode_input
from detGensim import detGensim as detLanguage

#stopwordsPath="./dysl/corpora/stopwords"

reload(sys)  
sys.setdefaultencoding('utf8')

config = {
	'modelFile' : '',
	'stopwordsPath' : ''}

def load_config(filename='', debug=False):
    confi_file = filename
    fd = open(confi_file, 'r')
    for line in fd.readlines():
        if ':' in line:  #line.startswith('SOAP'):
            k,v = line.split(':')
            config[k] = v.strip()
    fd.close()
    if debug:
       	print config

#class LangID(LM):
class LangID:
    """ Language Identification Class
    """

    def __init__(self):

        # Shall we mark some text as unk,
        # if top languages are too close?
        self.unk =False
        self.min_karbasa = 0.08

        # LM Parameters
        ngram = 3
        lrpad = u' '
        verbose = False
        corpus_mix = 'l'

        self.lm = LM(n=ngram, verbose=verbose, lpad=lrpad, rpad=lrpad,
                     smoothing='Laplace', laplace_gama=0.1,
                     corpus_mix=corpus_mix)

        self.trainer = None
        self.training_timestamp = 0

    @classmethod
    def _readfile(cls, filename):
        """ Reads a file a utf-8 file,
            and retuns character tokens.

            :param filename: Name of file to be read.
        """
        f = codecs.open(filename, encoding='utf-8')
        filedata = f.read()
        f.close()
        tokenz = LM.tokenize(filedata, mode='c')
        #print tokenz
        return tokenz

    #List Languages in a model file - CLARISSA
    def listLanguages(self):
	languages = []
	for key in self.lm.doc_lengths:
		languages.append (key)
  	return languages

    #Use PreLoad Corpus - CLARISSA
    def trainPRELOAD(self, filename, add=False):
	#'/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus.obj'
	if os.path.exists(filename):
		with open(filename, 'rb') as input:
			self.lm = pickle.load(input)

    #Create PreLoad Corpus - CLARISSA
    def trainORIGINAL(self,root,filename='./trainedCorpus.obj'):
        """ Trains our Language Model.

            :param root: Path to training data.
        """

        self.trainer = Train(root)
        corpus = self.trainer.get_corpus()
        for item in corpus:
            self.lm.add_doc(doc_id=item[0], doc_terms=self._readfile(item[1]))


	#CREATE PRELOAD CORPUS FILE - CLARISSA
	#filename='/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus.obj'
	if os.path.exists(filename):
	    os.remove(filename)
	with open(filename, 'wb') as output:
		pickle.dump(self.lm, output, pickle.HIGHEST_PROTOCOL)

        # Save training timestamp
        self.training_timestamp = self.trainer.get_last_modified()

   
    def add_sample(self, text=u'',  lang='', model_file = ''):
        """ Saves data previously added via add_training_sample().
            Data saved in folder specified by Train.get_corpus_path().

            :param domain: Name for domain folder.
                           If not set, current timestamp will be used.
            :param filename: Name for file to save data in.
                             If not set, file.txt will be used.

            Check the README file for more information about Domains.
        """
	print text,  lang, model_file
	self.lm.add_doc(doc_id=lang, doc_terms=[ch for ch in text.decode(encoding='UTF-8')])
	#CLARISSA - ADD NEW SENTENCES TO THE MODEL FILE
	if os.path.exists(model_file):
	    os.remove(model_file)
	
	with open(model_file, 'wb') as output:
		pickle.dump(self.lm, output, pickle.HIGHEST_PROTOCOL)
	return True

    def save_training_samples(self, domain='', filename='', text=u'',  lang=''):
        """ Saves data previously added via add_training_sample().
            Data saved in folder specified by Train.get_corpus_path().

            :param domain: Name for domain folder.
                           If not set, current timestamp will be used.
            :param filename: Name for file to save data in.
                             If not set, file.txt will be used.

            Check the README file for more information about Domains.
        """
        # self.trainer.save(domain=domain, filename=filename) OLD
	self.lm.add_doc(doc_id=lang, doc_terms=[ch for ch in text])
	#print "KJK",filename
	#CLARISSA - ADD NEW SENTENCES TO THE MODEL FILE
	if os.path.exists(filename):
	    os.remove(filename)
	with open(filename, 'wb') as output:
		pickle.dump(self.lm, output, pickle.HIGHEST_PROTOCOL)

    def replace_char_aux(self,text):
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
	return (text)

    def get_lang_set(self):
        """ Returns a list of languages in training data.
        """
        return self.trainer.get_lang_set()

    #FUNCTION FROM LDIG.PY
    def normalize(self,text): 
	    """normalization for twitter"""
	    text = re.sub(r'(@|#|https?:\/\/)[^ ]+', '', text)
	    text = re.sub(r'(^| )[:;x]-?[\(\)dop]($| )', ' ', text)  # facemark
	    text = re.sub(r'(^| )(rt[ :]+)*', ' ', text)
	    text = re.sub(r'([hj])+([aieo])+(\1+\2+){1,}', r'\1\2\1\2', text, re.IGNORECASE)  # laugh
	    text = re.sub(r' +(via|live on) *$', '', text)
	    return text

    #NEW CLASSIFY FUNCTION THAT implement the `identification` function to return full list of languages + probabilities. 
    #The oficial one - Identifies Chinese
    #CLARISSA
    def classifyReturnAll(self, text=u'',stopwordsPath=''):
        """ Predicts the Language of a given text.

            :param text: Unicode text to be classified.
        """
        #CLARISSA - delete special chars and punctuation to improve lang detection
        l = LangID()
        text = re.sub('[.,!@#$<>:;}?{()+-=-_&*@|\/"]+', '', text)
	text = self.normalize(text)
	text = self.replace_char_aux(text)
	
        text = self.lm.normalize(text)
	res = []
	ret = []
    	if (len(text) > 0) :

    		tokenz = [ch for ch in text] #LM.tokenize(text, mode='c')
    
    		result = self.lm.calculate(doc_terms=tokenz)

    		dif = 0
    		c = 0
    		lang = ''
    		langs = result['doc_id']
    		lang2 = ''
    		sum_others = 0
    		for p in result['all_probs']:	    
    		    if p != result['prob'] and p < dif and p < 0:
    			dif = p
    			lang2 = langs[c]
    			sum_others = sum_others + result['prob']
    		    elif p == result['prob']:
    			lang = langs[c]
    		    c = c + 1
    		dif = result['prob'] - dif

		
    		#print dif, lang, lang2,  (lang2 in ['az','tr'])  ,  (lang in ['az','tr']) , (dif > -30)

		#CLARISSA: may be unknown : little difference, except for Spanish and Portuguese get language with gemsym OR az and tr
    		if ((lang2 in ['az','tr'])  and  (lang in ['az','tr']) ) or (((lang2 != 'pt')  and  (lang != 'es')) or ((lang != 'pt')  and  (lang2 != 'es')))  and (dif > -15) and (len(text.split()) > 1) and (sum_others < 0): 

		    det = detLanguage(stopwordsPath)
		    language = det.detect_language(text)
    
    		    if len(language) > 3: #it is one of the languages we should learn
    			    lang = 'unk'
    		#CLARISSA
    		if (result['seen_unseen_count'][0]==0) or ( ((lang != 'unk')  and (lang != 'pt')  and  (lang != 'es') ) and ( (self.unk and self.lm.karbasa(result) < self.min_karbasa) or (len(lang) > 2))):
    		    lang = 'unk'
    		elif (lang != 'unk')  and (lang != 'pt')  and  (lang != 'es') :
    		    lang = result['calc_id']


		if (lang != 'unk'):


			n = 0
			while n < len(result['all_probs']):
				res.append([result['all_probs'][n],result['doc_id'][n]])
				n = n+1
			res = sorted(res)
			#print "res = ",res

			n = 0
			total = 0
			ret = []

			while (n < len(res)) and (res[n][0] < 0) :
				total = total + res[n][0]
				ret.append ( res[n] )
				n = n + 1

			if n > 0:
				for x in range(0, n):
					ret[x][0] = (ret[x][0] / total)

		else: #chinese
			#Chinese
			#print result['calc_id'],'len(result)',len(result['doc_id'])
			zh = False		
			for n in re.findall(ur'[\u4e00-\u9fff]+',text):
				zh = True
				#'actual_id': ''
			if zh:
				ret = [[1,'zh']]

	return (ret)	

   
if __name__ == '__main__':

    l = LangID()
    l.trainORIGINAL('/home/ccx/work/dysl/dysl/corpora/multiLanguage','/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus.obj')
    #l.trainPRELOAD('/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus.obj', False)
    #l.add_sample('português',  'pt', '/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus.obj')
    #print l.listLanguages()
    #print l.classifyReturnAll('portuguÊs','/home/ccx/work/dysl/dysl/corpora/stopwords')
    #print l.classifyReturnAll('sdsd sdsd sdsd sffff','/home/ccx/work/dysl/dysl/corpora/stopwords')

