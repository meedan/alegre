# coding=UTF-8
from collections import OrderedDict
from alphabet_detector import AlphabetDetector
from gensim import corpora, models, similarities, utils, matutils
from gensim.models import word2vec
import re
import os
import sys  
import hanzidentifier
import pickle
from operator import itemgetter

class LangId:     
  def __init__(self):
    modelPath = os.path.dirname(os.path.abspath(__file__))+'/model'
    if modelPath.endswith('/'):
      modelPath = modelPath[:-1]
    self.modelPath = modelPath
    self.initVars()
    self.SWinitVars(modelPath+'/stopwords/')

  def SWinitVars(self, mypath):
    self.SWlangIds = []
    self.SWvecs = {}
    self.SWmodel = {}
    if mypath.endswith('/'):
      mypath = mypath[:-1]
    for filename in os.listdir(mypath):
      self.SWvecs[filename] = vec(mypath+"/"+str(filename))
      self.SWmodel[filename] = word2vec.Word2Vec(self.SWvecs[filename].ss, size=2, min_count=1)

  def initVars(self):
    reload(sys)  
    sys.setdefaultencoding('utf8')
    f = open(self.modelPath+'/languages', 'r')
    self.languages = f.read().split('\n')
    self.languages.pop()	


    if os.path.exists(self.modelPath+'/corpus.mm'):
      self.dictionary = corpora.Dictionary.load(self.modelPath+'/dict.dict')
      self.corpus = corpora.MmCorpus(self.modelPath+'/corpus.mm')
      self.tfidf = models.TfidfModel.load(self.modelPath+'/model.tfidf')
      self.documents = pickle.load(open(self.modelPath+'/documents.obj', "rb" ) )
      self.w2v = models.Word2Vec.load(self.modelPath+'/model.w2v')
      self.w2v.save(self.modelPath+'/model.w2v') # same for tfidf, lda, ...

      self.texts = []
      for document in self.documents:
          self.texts.append(document) #.lower().split())   

    else:
      self.documents = []
      for lang in self.languages:
        self.documents.append(self.readFile(self.modelPath+'/'+lang.lower()))

      self.texts = []
      for document in self.documents:
          self.texts.append(document) #.lower().split())   

      self.newModelFiles()




  def newModelFiles(self):
      
    self.dictionary = corpora.Dictionary(self.texts)
    self.corpus = [self.dictionary.doc2bow(text) for text in self.texts]
    self.dictionary.save(self.modelPath+'/dict.dict')
    corpora.MmCorpus.serialize(self.modelPath+'/corpus.mm', self.corpus)
    

    self.tfidf = models.TfidfModel(self.corpus) # step 1 -- initialize a model
    self.tfidf.save(self.modelPath+'/model.tfidf') # same for tfidf, lda, ...

    self.w2v = models.Word2Vec(self.documents) # step 1 -- initialize a model
    self.w2v.save(self.modelPath+'/model.w2v') # same for tfidf, lda, ...
    

    pickle.dump(self.documents, open(self.modelPath+'/documents.obj', "wb" ) )

  def SWsimilar(self,model,v,txt):
    doc_tokens = txt.lower().split()
    w = filter(lambda x: x in v.ss2, doc_tokens)
    dif = len(doc_tokens) - len(w)  
    ##print "===",w,dif,len(doc_tokens) , len(w) ,v.ss2
    if len(w) > 0:
      try:
        return model.n_similarity(v.ss2, w) - dif
      except Exception, e:
        return dif * -1
    else:
      return dif * -1

  def SWdetect_language(self,text):
    sim = []
    n = 0
    for item in self.SWmodel:
      ##print item
      sim = self.SWsimilar(self.SWmodel[item],self.SWvecs[item],text)
      ##print sim
      if (n == 0) or (n < sim):
        lang = item
        n = sim
  
    ##print "return ",lang
    if (n == (len(text.lower().split()) * -1)):
      return ""
    else:
      return lang      


  def sim_tfidf(self, doc):
      
      try:
        vec_bow = self.dictionary.doc2bow(doc)#.lower().split())
        vec_tfidf = self.tfidf[vec_bow] # convert the query to LSI space
        index = similarities.MatrixSimilarity(self.tfidf[self.corpus])
        sims = index[vec_tfidf]
        #print '-TFIDF->',sorted(enumerate(sims), key=lambda item: -item[1])
        #return sorted(enumerate(sims), key=lambda item: -item[1])

        return sorted(enumerate(sims), key=lambda item: -item[1])
      except ValueError:
        return []

  def threeGrams(self,b):
    n = 3
    ret = []
    for i in range(0, len(b), 1):
      ret.append(b[i:i+n])
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
      text = re.sub('«»“”"[.,!%@#$<>:;}?{()+-=-_&*@|\/"]+', ' ', text)
      text = re.sub('(\!|#|\*|\?|,|;|:|%|\$|\"|\.\.\.)', ' ', text)

      text = re.sub('  +', ' ', text)
      text = re.sub('hahaha', '', text)
      text = re.sub('haha', '', text)
      text = re.sub('(\sx\s|\sX\s)+', ' ', text)
      text = re.sub('(\😌|\✨|\➡|\⬅|\☕️|\😂|\😃|\😎|\😁|\😢|\😉|\😴|\😊|\♡|\😚|\😘|\😍|\💕|\💓|\💙|\💛|\💖|\💜|\💞|\🎉|\💗|\🔛)+', '', text)
      text = re.sub('(؟|\/|\t|\n+| - |\.)', ' ', text)
      text = re.sub(r'\\', ' ', text)
      text = re.sub('\[', '', text)
      text = re.sub('\]', '', text)
      text = re.sub('\(', '', text)
      text = re.sub('\)', '', text)
      text = re.sub('(  )+', ' ', text)
      while text.endswith(' ') or text.endswith('\n'):
        text = text[:-1]
      return text


  
  def readFile(self,filesPath):
    i = []# u''
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
     langPreDefined = ''
     if hanzidentifier.has_chinese(text): #chinese
       chineseArray = re.findall(ur'[\u4e00-\u9fff]+',text)
       chineseChars = len(str(chineseArray)) - (2+len(chineseArray))

       if len(text) / 3 < chineseChars: #At least 1/3 of the sentence in Chinese characteres
         if hanzidentifier.identify(text) is hanzidentifier.SIMPLIFIED:
           ret = [[1,'ZH-CHS']]
         elif hanzidentifier.identify(text) is hanzidentifier.TRADITIONAL:
           ret = [[1,'ZH-CHT']]
         elif hanzidentifier.identify(text) is hanzidentifier.BOTH:
           ret = [[1,'ZH-CHT'],[1,'ZH-CHS']]

     #not chinese    
     if len(ret) == 0:
       sims = self.sim_tfidf(self.threeGrams(text))

       if len(sims) > 0:
        language = ''
        #sims = self.stopwordsIncreaseSims (text,sims)

        dLanguages = {}
        for s in sims:
          if s[1] > 0:
            dLanguages[self.languages[s[0]].lower()] = s[1]

        lang1= self.languages[sims[0][0]].lower()
        lang2= self.languages[sims[1][0]].lower()

        print '......',text,sims,lang1,lang2,((sims[0][1] - sims[1][1]) > 0.003) , (sims[0][1] > 0.004)
        if ( ((sims[0][1] - sims[1][1]) > 0.003) and (sims[0][1] > 0.004) ) or (self.arabicAndfarsi(lang1, lang2, text)):
          language = self.languageRules(lang1, lang2, dLanguages, text)
          ##print "---> ",language
          if len(language) > 0:
            ret.append([1, str(language.upper())])
            langPreDefined = language.upper()
        else:
          #print "ICI",self.languages
          lang = ""
          language = self.SWdetect_language(text)
  
          if len(language) > 0:
            ret.append([1, str(language.upper())])
            langPreDefined = language.upper()

        for s in sims:
          if (self.languages[s[0]] != langPreDefined):
            ret.append( [ str(s[1]), str(self.languages[s[0]])])

     return ret

  def arabicAndfarsi(self, lang1, lang2, text):
    if ((lang2 == 'ar')  and  (lang1 == 'fa') ) or ((lang1 == 'ar')  and  (lang2 == 'fa') ):     
      return True
    else:
      return False

  def findInText(self, chars, text):
    for ch in chars:
      if text.find(ch) > -1:
        return True
    return False

  def languageRules(self, lang1, lang2, dLanguages, text):
    language = ''




    if 'tl' in dLanguages.keys():
      if text.find(' pa ') > -1:
        language = 'tl'  
      if ( text.find(' na ') > -1) and ((lang1 != 'pt')  and  (lang2 != 'pt') ):
        language = 'tl'

    if ((lang1 == 'id')  and  (lang2 == 'tr') ):     
      if text.find('ş') > -1:
        language = 'tr'
    elif ((lang1 == 'tr')  and  (lang2 == 'az') ):     
      if text.find('ə') > -1:
         language = 'az'

    elif ((lang2 == 'ar')  and  (lang1 == 'fa') ) or ((lang1 == 'ar')  and  (lang2 == 'fa') ):     
      if self.findInText(['ﻩو','ة','دو'], text):
        language = 'ar'
      elif self.findInText(['دوازده','وﻩ',' و ','پ','چ','ژ','گ'], text):       
        language = 'fa'  


    elif ((lang2 == 'en')  and  (lang1 == 'az') ) or ((lang1 == 'en')  and  (lang2 == 'az') ):     
      if (text.find('ç') > -1) or  (text.find('ə') > -1) or (text.find('ş') > -1):
         language = 'az'
      elif (text.find(' to ') > -1) or (text.find(' day ') > -1) or (text.find(' one ') > -1):
         language = 'en'  

    elif ((lang2 == 'en')  and  (lang1 == 'id') ) or ((lang1 == 'en')  and  (lang2 == 'id') ):     
      if (text.find("i'm") > -1) or (text.find(' for') > -1) or  (text.find('thy') > -1) or (text.find('ts') > -1) or (text.find(' my ') > -1) or (text.find(' are ') > -1) or (text.find("aren't") > -1):
         language = 'en' 

    elif ((lang2 == 'en')  and  (lang1 == 'pt') ) or ((lang1 == 'en')  and  (lang2 == 'pt') ):     
      if (text.find('you') > -1):
         language = 'en' 

    elif ((lang2 == 'en')  and  (lang1 == 'es') ) or ((lang1 == 'en')  and  (lang2 == 'es') ):     
      if (text.find('you') > -1):
         language = 'en' 
      elif (text.find('leer') > -1):
         language = 'es' 

    elif ((lang2 != 'es')  and  (lang2 != 'fr')  and  (lang1 == 'tl') ) or ((lang1 != 'es')  and (lang1 != 'fr')  and  (lang2 == 'tl') ):     
      if (text.find(' ni ') > -1) :
         language = 'tl' 

    elif ((lang2 == 'id')  and  (lang1 == 'tl') ) or ((lang1 == 'id')  and  (lang2 == 'tl') ):     
      if (text.find('nasa') > -1) or (text.find(' at ') > -1)  or (text.find(' na ') > -1)  or (text.find('sila ') > -1) :
         language = 'tl' 

    elif ((lang2 == 'en')  and  (lang1 == 'tl') ) or ((lang1 == 'en')  and  (lang2 == 'tl') ):     
      if (text.find('easy') > -1):
         language = 'en' 

    elif ((lang2 == 'en')  and  (lang1 == 'fr') ) or ((lang1 == 'en')  and  (lang2 == 'fr') ):     
      if (text.find(' this') > -1) or (text.find('will') > -1) or (text.find(' one') > -1) or (text.find('ee') > -1) :
         language = 'en' 
      elif (text.find('è') > -1):
         language = 'fr' 
    elif ((lang2 == 'en')  and  (lang1 == 'it') ) or ((lang1 == 'en')  and  (lang2 == 'it') ):     
      if (text.find('thy') > -1) or (text.find('well') > -1) or (text.find('ts') > -1) or (text.find('ing ') > -1):
         language = 'en' 
      if (text.find('è') > -1):
         language = 'it' 

    elif ((lang1 == 'es')  and  (lang2 == 'en') ):     
      if (text.find('my') > -1) or (text.find('ck') > -1):
         language = 'en' 
    elif ((lang1 == 'it')  and  (lang2 == 'es') ):     
      if (text.find('nn') > -1) or (text.find('à') > -1)  or (text.find('ù') > -1):
         language = 'it' 
      elif (text.find('ñ') > -1) or (text.find(' ni ') > -1):
         language = 'es'
      else:
         language = self.SWdetect_language(text)
    elif ((lang1 == 'pt')  and  (lang2 == 'es') ) or ((lang2 == 'pt')  and  (lang1 == 'es') ): 
      if (text.find('ñ') > -1) or (text.find('ll') > -1) or (text.find(' y ') > -1)  or (text.find(' el ') > -1)  or (text.find(' hay') > -1):
         language = 'es'
      elif (text.find('ç') > -1) or (text.find(' e ') > -1)  or (text.find('à') > -1):
         language = 'pt'

    return language

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

class vec:
  def __init__(self, fi):
    self.ss = []
    self.ss2=[]
    for line in open(fi):
      self.ss.append([line.replace("\n", "").lower()])
      self.ss2.append(line.replace("\n", "").lower())



def rFile(filesPath):
    ss=[]
    for file in os.listdir(filesPath):
      if file.endswith(".txt"):
        for line in open(filesPath+'/'+file):
          line = threeGrams(l.normalize(line))
          ##print line
          ss.append(line.split())
    return ss

def threeGrams(b):
      ret = ''
      for term in b.split(' '):
        if len(term) > 0:
          if len(term) == 1:
            ret = ret + term + ' '
          else:
            for i in range(len(term)-1):
              ret = ret +  term[i:i+3] + ' '
      return ret



def sameAlphabet(vLine):
  ad = AlphabetDetector()
  if len (ad.detect_alphabet(vLine.decode('utf-8'))) <= 1:
    return True
  else:
    return False

def canBeEnglish(res,window):
  if window == 3 :
    if ((res[0][1].upper() == 'EN') and (float(res[0][0]) > 0)) or ((res[1][1].upper() == 'EN') and (float(res[1][0]) > 0)) or ((res[2][1].upper() == 'EN') and (float(res[2][0]) > 0)): #one of the first three languages is English
      return True
  elif window == 4 :
    if ((res[0][1].upper() == 'EN') and (float(res[0][0]) > 0)) or ((res[1][1].upper() == 'EN') and (float(res[1][0]) > 0)) or ((res[2][1].upper() == 'EN') and (float(res[2][0]) > 0))  or ((res[3][1].upper() == 'EN') and (float(res[3][0]) > 0)): #one of the first three languages is English
      return True

  return False

def difFirstSecond(res):
  if (float(res[0][0]) < 1) and (float(res[0][0]) > 0) and (float(res[1][0]) > float(res[0][0]) / 3):
    return True
  else:
    return False

def classifyWindow3Words(line):  
  res = l.classify(line)
  resOriginal = res 
  print 'line,res -><',line,res
  if len(res) > 2: #[['0.196574', 'ES'], ['0.0847508', 'EN'],
    ##print '----++',line, res
    if  (not sameAlphabet(line)) or ( difFirstSecond(res) and canBeEnglish(res,3) )  :
      dLangs = {}
      vLine = line.split(' ')

      while len(vLine[0]) < 1:
        vLine.pop(0)

      n = 0
      vLangs = []
      #first window

      while len(vLine) > 3:
        while len(vLine[0]) < 1:
          vLine.pop(0)
        w1 = vLine[0]+' '+vLine[1]+ ' '+vLine[2]
        if (sameAlphabet(w1)):
          lang = l.classify(w1)
          lang[0][1] = areEnID(lang)
          ##print '....',w1,lang
          vLangs.append([w1,lang])

          if len(lang) > 0:
            if lang[0][1] in dLangs:
              dLangs[lang[0][1]] += 1
            else:
              dLangs[lang[0][1]] = 1

        vLine.pop(0)

      ##print 'vline',len(vLine),vLine
      if len(vLine) > 0:
        w1 = ''
        for w in vLine:
          w1 = w1+' '+w
        if len(w1) > 2 and (sameAlphabet(w1)):  
          w1 = w1[1:] #remove first char

          lang = l.classify(w1)
          lang[0][1] = areEnID(lang)
          #print 'x....',w1,lang
          vLangs.append([w1,lang])


          if len(lang) > 0:
            if lang[0][1] in dLangs:
              dLangs[lang[0][1]] += 1
            else:
              dLangs[lang[0][1]] = 1


        #dLangs in res
        res = []
        for key, value in dLangs.iteritems():
          res.append([value,key])
      if ('EN' in dLangs) and (len(dLangs)>1):
        return  sorted(formatRet2(formatRet1(percentageResult(res))).items(), key=lambda item: -item[1])
      else:
        return sorted(formatRet1(percentageResult(resOriginal)).items(), key=lambda item: -item[1]) 


  ##print 'line,res -RET -',res[0][0],res
  if float(res[0][0]) > 0:
    return sorted(formatRet1(percentageResult(res)).items(), key=lambda item: -item[1]) 
  else:
    return []


def areEnID(lang):
  #[are] in id and en
  if lang[0][1] == 'ID' and lang[1][1] == 'EN':
    if ' are ' or "aren't" in w1:
      return 'EN'
  return (lang[0][1])

def formatRet1(ret):
  retDict = {}
  for r in ret:   
    retDict[r[1]] = r[0]

  return retDict

  #in: [[0.5333333333333333, 'EN'], [0.28888888888888886, 'ES'], [0.06666666666666667, 'IT'], [0.044444444444444446, 'TL'], [0.044444444444444446, 'FR'], [0.022222222222222223, 'ID']]
  #out: `{ [en,ar]: 0.48 , [en,fa]: 0.32 , [fr,ar]: 012 , [fr,fa]: 0.08 }` 

def formatRet2(retDict1):
  retDict2 = {}
  for key, value in retDict1.iteritems():
    if key != 'EN':
      retDict2['[EN,'+str(key)+']'] = value + retDict1['EN']

  return retDict2
  #in: [[0.5333333333333333, 'EN'], [0.28888888888888886, 'ES'], [0.06666666666666667, 'IT'], [0.044444444444444446, 'TL'], [0.044444444444444446, 'FR'], [0.022222222222222223, 'ID']]
  #out: `{ [en,ar]: 0.48 , [en,fa]: 0.32 , [fr,ar]: 012 , [fr,fa]: 0.08 }` 


def percentageResult (res):
  totalSum = 0
  n = 0
  for r in res:
    totalSum = totalSum + float(r[0]) 

  for r in res:
    res[n][0] = float(r[0]) / float(totalSum)
    n = n + 1


  return (res)



def testWindow3Words(fd,f):
  res = []
  for line in fd.readlines():
    line = l.normalize(re.sub('\n', '', line))
    result = classifyWindow3Words(line)
    #print str(line),result
    f.write(str(line)+'\t'+str(result)+'\n')
    f.flush()

if __name__ == '__main__':

  l = LangId()
  if True: #False: #
    line = l.normalize("enjoy na enjoy ang crowd")
    # (" The system is highly useful for linguists and ethnographers to categorize the  هو واحد من أوائل المستوطنين الأمريكيين، وزعيم إقليمي في ما يُعرف الآن بمقاطعة بروارد في ولاية فلوريدا الأمريكية. قتلت السيمينول عائلته عام 1836، خلال حرب السيمينول الثانية، languages spoken on a regional basis, and to compute analysis in the field of lexicostatistics ") #("el caballo es de color marrón fuerte: the horse is very brown");#"يستقبل رئيس النائب في هذه الأثناء رئيسة بعثة في كريستينا لاسن : Receives the President of MP in the meantime, Head of Mission, Christina Lassen") #2,11    
    #print "line->",line
    #line = normalize("can you help me هل بإمكانك مساعدتي")
    result = classifyWindow3Words(line)
    print str(line),result

  else:
    #f = open('./rtestPosts.txt', 'w')
    #fd = open('./testPosts.txt', 'r')
    #f = open('./raren.txt', 'w')
    #fd = open('./aren2.txt', 'r')
    f = open('./reval.txt', 'w')
    fd = open('./eval.txt', 'r')
    testWindow3Words (fd,f)
    #test3(fd,f)
    fd.close()
    '''
    
    #print '=================='
    fd = open('./esen.txt', 'r')
    test3(fd,f)
    fd.close()
    #print '=================='
    fd = open('./es.txt', 'r')
    test(fd,f)
    fd.close()
    '''
    f.close()
