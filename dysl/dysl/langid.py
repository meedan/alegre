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

    def __init__(self, unk=False):

        # Shall we mark some text as unk,
        # if top languages are too close?
        self.unk = unk
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
	#print vars(self.trainer)

        # Show loaded Languages
        #print 'Lang Set: ' + ' '.join(train.get_lang_set())

        for item in corpus:
            self.lm.add_doc(doc_id=item[0], doc_terms=self._readfile(item[1]))
	    #print "self.lm.add_doc(doc_id=item[0], doc_terms=self._readfile(item[1]))",item[0], self._readfile(item[1])
	'''
	print "dir(self.lm) = ,",dir(self.lm)
	print "vars(self.lm.smoothing) = ,",self.lm.smoothing
	print "vars(self.lm.corpus_count_n)",self.lm.corpus_count_n
	print "vars(self.lm.corpus_count_n_1)",self.lm.corpus_count_n_1
	print "vars(self.lm.doc_lengths)",self.lm.doc_lengths
	print "DUMP INIT"
	'''

	#CREATE PRELOAD CORPUS FILE - CLARISSA
	#filename='/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus.obj'
	if os.path.exists(filename):
	    os.remove(filename)
	with open(filename, 'wb') as output:
		pickle.dump(self.lm, output, pickle.HIGHEST_PROTOCOL)

        # Save training timestamp
        self.training_timestamp = self.trainer.get_last_modified()

    def is_training_modified(self):
        """ Returns `True` if training data
            was modified since last training.
            Returns `False` otherwise,
            or if using builtin training data.
        """

        last_modified = self.trainer.get_last_modified()
        if last_modified > self.training_timestamp:
            return True
        else:
            return False

    def was_training_modified(self):
        """ For Grammar Nazis, 
            just alias for is_training_modified()
        """
        return self.is_training_modified()


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

    def get_lang_set(self):
        """ Returns a list of languages in training data.
        """
        return self.trainer.get_lang_set()

    #NEW CLASSIFY FUNCTION THAT implement the `identification` function to return full list of languages + probabilities. 
    #CLARISSA
    def classifyReturnAll(self, text=u'',stopwordsPath=''):
        """ Predicts the Language of a given text.

            :param text: Unicode text to be classified.
        """
        #CLARISSA - delete special chars and punctuation to improve lang detection
        l = LangID(unk=False)
        text = re.sub('[.,!@#$<>:;}?{()+-=-_&*@|\/"]+', '', text)
	char_aux = '✈'
	text = text.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '❤'
	text = text.replace(char_aux.decode(encoding='UTF-8'), "")
        text = self.lm.normalize(text)
	res = []
	ret = []
    	if (len(text) > 0) :
    		tokenz = LM.tokenize(text, mode='c')
    
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

		#CLARISSA: may be unknown : little difference, except for Spanish and Portuguese get language with NLTK
    		if   (((lang2 != 'pt')  and  (lang != 'es')) or ((lang != 'pt')  and  (lang2 != 'es')))  and (dif > -15) and (len(text.split()) > 1) and (sum_others < 0): 

    		    #det = detLanguage()
    		    #language = det.detect_language(text)
		    print "stopwordsPath", stopwordsPath
		    det = detLanguage(stopwordsPath)
		    language = det.detect_language(text)
    
    		    if len(language) > 3: #it is one of the languages we should learn
    			    lang = 'unk'
    		#CLARISSA
	        #print  result['seen_unseen_count'][0],"==0) or ( ((",lang," != 'unk')  and (",lang," != 'pt')  and  (",lang," != 'es') ) and ( (",self.unk," and ",self.lm.karbasa(result)," < ",self.min_karbasa,") or (",len(lang)," > 2))):"
    		if (result['seen_unseen_count'][0]==0) or ( ((lang != 'unk')  and (lang != 'pt')  and  (lang != 'es') ) and ( (self.unk and self.lm.karbasa(result) < self.min_karbasa) or (len(lang) > 2))):
    		    lang = 'unk'
    		elif (lang != 'unk')  and (lang != 'pt')  and  (lang != 'es') :
    		    lang = result['calc_id']
                #print "result['calc_id'] = ",result['calc_id']

		if (lang != 'unk'):


			n = 0
			while n < len(result['all_probs']):
				res.append([result['all_probs'][n],result['doc_id'][n]])
				n = n+1
			res = sorted(res)

			n = 0
			total = 0
			ret = []

			while res[n][0] < 0:
				total = total + res[n][0]
				ret.append ( res[n] )
				n = n + 1

			if n > 0:
				for x in range(0, n):
					ret[x][0] = (ret[x][0] / total)

		
	return (ret)	


    #NEW CLASSIFY FUNCTION THAT CALLS THE OLD ONE
    #SET AS UNK MULTI-LANGUAGE TEXTS
    #CLARISSA
    def classifyNOT(self, text=u''):
	print "TEXT = ",text
	return text

    def classify(self, text=u'', stopwordsPath=''):

	if (stopwordsPath == ''):
		load_config(filename='../config.yml', debug=False)
		stopwordsPath = config['stopwordsPath']

	lang = self.classify2(text.encode('utf-8'), stopwordsPath)

	if lang != 'unk':

		#Split in senteces to see if multilingual
		text2 = text
		text2 = text2.replace(".","#")
		text2 = text2.replace(";","#")
		text2 = text2.replace("!","#")
		text2 = text2.replace("?","#")
		text2 = text2.replace("/","#")
		text2 = text2.replace(":","#")
		text2 = text2.replace("(","#")
		text2 = text2.replace(")","#")
		sentences = text2.split("#")

		# for each word in the line:
		for sent in sentences:
			if len(sent) > 1:
				lang2 = self.classify2(sent,stopwordsPath)
				#print len(sent), lang2,' != ',lang, sent
				if lang2 != 'unk' and lang2 != lang:
					lang = 'unk'
	return lang

    #OLD CLASSIFY FUNCTION
    def classify2(self, text=u'', stopwordsPath=''):
        """ Predicts the Language of a given text.

            :param text: Unicode text to be classified.
	        """
	print 'xx stopwordsPath, ',stopwordsPath

        #CLARISSA - delete special chars and punctuation to improve lang detection
        l = LangID(unk=False)
        text = re.sub('[.,!@#$<>:;}?{()+-=-_&*@|\/"]+', '', text)
	char_aux = '✈'
	text = text.replace(char_aux.decode(encoding='UTF-8'), "")
	char_aux = '❤'
	text = text.replace(char_aux.decode(encoding='UTF-8'), "")
        text = self.lm.normalize(text)
    	lang = ""
    	if (len(text) > 0) :
    		tokenz = LM.tokenize(text, mode='c')

    		result = self.lm.calculate(doc_terms=tokenz)
    		#print result
    		#CLARISSA: calculate the difference of probability from the languages, keep the 2 lowest and the sum of probs not picked
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
    		#print "result = ",result

	        #print result
		#print dif,"( > -15) and (",len(text.split())," > 1) and (",sum_others," < 0"
		print 'stopwordsPath, ',stopwordsPath
		print "TEXT gg = ",text
		#CLARISSA: may be unknown : little difference, except for Spanish and Portuguese get language with NLTK
    		if   (((lang2 != 'pt')  and  (lang != 'es')) or ((lang != 'pt')  and  (lang2 != 'es')))  and (dif > -15) and (len(text.split()) > 1) and (sum_others < 0): 

    		    #det = detLanguage()
    		    #language = det.detect_language(text)
		    print "stopwordsPath", stopwordsPath
		    det = detLanguage(stopwordsPath)
		    language = det.detect_language(text)
	    	    print "TEXT h = ",text
    
    		    if len(language) > 3: #it is one of the languages we should learn
    			    lang = 'unk'
	    	    print "TEXT i = ",text
    		#CLARISSA
	        #print  result['seen_unseen_count'][0],"==0) or ( ((",lang," != 'unk')  and (",lang," != 'pt')  and  (",lang," != 'es') ) and ( (",self.unk," and ",self.lm.karbasa(result)," < ",self.min_karbasa,") or (",len(lang)," > 2))):"
    		if (result['seen_unseen_count'][0]==0) or ( ((lang != 'unk')  and (lang != 'pt')  and  (lang != 'es') ) and ( (self.unk and self.lm.karbasa(result) < self.min_karbasa) or (len(lang) > 2))):
    		    lang = 'unk'
    		elif (lang != 'unk')  and (lang != 'pt')  and  (lang != 'es') :
    		    lang = result['calc_id']
                #print "result['calc_id'] = ",result['calc_id']
		return lang

if __name__ == '__main__':

    l = LangID(unk=False)
    l.train()

    if len(sys.argv) > 1:
        text_in = decode_input(sys.argv[1:])
    else:
        text_in = u'hello, world'

    lang_res = l.classify(text_in)
    #print text_in, '[ Language:', lang_res, ']'
