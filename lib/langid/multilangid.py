# coding=UTF-8
from gensim import corpora, models, similarities, utils, matutils
from gensim.models import word2vec
import re
import os
import sys  
import hanzidentifier
import pickle

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
    else:
      self.documents = []
      for lang in self.languages:
        self.documents.append(self.readFile(self.modelPath+'/'+lang.lower()))
        self.newModelFiles()

  def newModelFiles(self):
    self.texts = []
    for document in self.documents:
        self.texts.append(document.lower().split())         
    self.dictionary = corpora.Dictionary(self.texts)
    self.corpus = [self.dictionary.doc2bow(text) for text in self.texts]
    self.dictionary.save(self.modelPath+'/dict.dict')
    corpora.MmCorpus.serialize(self.modelPath+'/corpus.mm', self.corpus)
    self.tfidf = models.TfidfModel(self.corpus) # step 1 -- initialize a model
    self.tfidf.save(self.modelPath+'/model.tfidf') # same for tfidf, lda, ...
    pickle.dump(self.documents, open(self.modelPath+'/documents.obj', "wb" ) )

  def SWsimilar(self,model,v,txt):
    doc_tokens = txt.lower().split()
    w = filter(lambda x: x in v.ss2, doc_tokens)
    dif = len(doc_tokens) - len(w)  
    #print len(doc_tokens) , len(w)  
    if len(w) > 0:
      return model.n_similarity(v.ss2, w) - dif
    else:
      return dif * -1

  def SWdetect_language(self,text):
    sim = []
    n = 0
    for item in self.SWmodel:
      #print item
      sim = self.SWsimilar(self.SWmodel[item],self.SWvecs[item],text)
      #print sim
      if (n == 0) or (n < sim):
        lang = item
        n = sim
  
    #print "return ",lang
    if (n == (len(text.lower().split()) * -1)):
      return ""
    else:
      return lang      


  def sim_tfidf(self, doc):
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
        lang1= self.languages[sims[0][0]].lower()
        lang2= self.languages[sims[1][0]].lower()
        #print '---',sims,self.languages[sims[0][0]]        
        if False: # sims[0][1] > 0.004:
          language = self.languages[sims[0][0]]        
        else:
          lang = ""
          #print 'lang1,lang2',lang1,lang2,'self.languages',self.languages

          if ((lang1 == 'id')  and  (lang2 == 'tr') ):     
            if text.find('ş') > -1:
              language = 'tr'
          elif ((lang1 == 'tr')  and  (lang2 == 'az') ):     
            if text.find('ə') > -1:
               language = 'az'
          elif ((lang1 == 'it')  and  (lang2 == 'es') ):     
            if (text.find('nn') > -1) or (text.find('à') > -1):
               language = 'it' 
            if (text.find('ñ') > -1) or (text.find(' ni ') > -1):
               language = 'es'
            else:
               language = self.SWdetect_language(text)

          elif ((lang1 == 'pt')  and  (lang2 == 'es') ):     
            if (text.find('ñ') > -1) or (text.find('ll') > -1) or (text.find(' y ') > -1)  or (text.find(' el ') > -1):
               language = 'es'
            elif (text.find('ç') > -1) or (text.find(' e ') > -1)  or (text.find('à') > -1):
               language = 'pt'
            else:
               language = self.SWdetect_language(text)

          elif ((lang1 == 'fr')  and  (lang2 == 'en') ) or ((lang1 == 'id')  and  (lang2 == 'en')) or ((lang1 == 'it')  and  (lang2 == 'en')) or ((lang1 == 'fa')  and  (lang2 == 'ar') ):
             lang = self.SWdetect_language(text)
          #print "LA === ",language   
          if len(lang) > 0:
            language = lang
            ret.append ([[1, str(lang.upper())]])
          elif len(language) > 0:
            ret = ([[1, str(language.upper())]])
          else:
            #print "IINININ - sims",sims
            for s in sims:
              ret.append( [ str(s[1]), str(self.languages[s[0]])])

     return ret

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



def testWord(fd,f):
  for line in fd.readlines():
    line = re.sub('\n', '', line)
    print str(line)
    #f.write('++++ \t'+str(line)+'\n')
    words = line.split(' ')    
    for w in words:
      ll = str(line)+'\t'+str(w)+'\t'+str(l.classify(w))+'\n'
      print ll
      #f.write(ll)
  #f.write("======================\n")
  fd.close()

def test2(fd,f):
  res = []
  for line in fd.readlines():
    line = re.sub('\n', '', line)
    res = l.classify(line)
    #f.write('++++ \t'+str(line)+'\n')
    ll = str(line)+'\t'+str(res)+'\n'
    #print ll
    if (res[0][1] == 'EN') or (res[1][1] == 'EN') or (res[2][1] == 'EN'):
      print line
      print 'EN->',modelMatch('./model/en','./model/en/model.w2v',line.lower())
      print 'ES->',modelMatch('./model/es','./model/es/model.w2v',line.lower())
      #f.write(ll)
  #f.write("======================\n")
  fd.close()

def modelMatch(f,m,line):
  if not (os.path.exists(m)):
    vocab = rFile(f)
    #print 'sentences',len(vocab),vocab
    model =  word2vec.Word2Vec(vocab, min_count=0)
    #model.save(m)
  else:
    model = word2vec.Word2Vec.load(m)

  line = threeGrams(line)
  doc_tokens = line.split()

  print 'line_',len(model.vocab)
  #print model.similarity('alk', 'lke')
  #https://github.com/piskvorky/gensim/issues/310
  w = filter(lambda x: x in model.vocab, doc_tokens)
  print 'w->',len(w),w



  #for x in model.vocab:
    #print x
  '''  
  print model.score(line)
  try:  
    ret = model.doesnt_match(line.split())
    return (ret)        
  except ValueError:
  '''
  return ([])

def rFile(filesPath):
    ss=[]
    for file in os.listdir(filesPath):
      if file.endswith(".txt"):
        for line in open(filesPath+'/'+file):
          line = threeGrams(normalize(line))
          #print line
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

def normalize(text): 
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


      text = re.sub('(؟|\/|\t|\n+| - |\.)', ' ', text)
      text = re.sub(r'\\', ' ', text)
      text = re.sub('\[', '', text)
      text = re.sub('\]', '', text)
      text = re.sub('\(', '', text)
      text = re.sub('\)', '', text)
      text = re.sub('(  )+', ' ', text)
      return text

#if one part is [lang,1] and full doc top similarity is lang, then return lang
def test3(fd,f):
  model = word2vec.Word2Vec.load('./brownmodel.w2v')
  #for line in fd.readlines():
  if True:
    #line = 'me/ you  him/ her  خد'
    line = "i'm fine as a whole"
    line = normalize(line)
    doc_tokens = line.split()
    words = filter(lambda x: x in model.vocab, doc_tokens)
    engl = ''

    if len(words)>0:
      engl = line[line.find(words[0]):(line.rfind(words[-1])+len(words[-1]))]
      classEngl = [['1','EN']]
      print '_',engl,classEngl

      #print 'line.find(words[0])',line.find(words[0]),line.rfind(words[len(words)-1])
      print "line",line,words,'-',engl

      other =  line.replace(engl,"")
      otherLang = l.classify(other)
      
      if len(classEngl)<1:
        classEngl.append(['',''])
      if len(otherLang)<1:
        otherLang.append(['',''])

      ll = str(line)+'\t'+str(engl)+'\t'+str(classEngl[0][1])+'\t'+str(classEngl)
      ll = ll+'\t'+str(other)+'\t'+str(otherLang[0][1])+'\t'+str(otherLang)+'\n'
      f.write(ll)
      print ll
    else:
      other =  line
      otherLang = l.classify(other)
      ll = str(line)+'\t'+''+'\t'+''+'\t'+''+'\t'+str(other)+'\t'+str(otherLang[0][1])+'\t'+str(otherLang)+'\n'
      f.write(ll)
      print ll

def testWindow3Words(fd,f):
  res = []
  for line in fd.readlines():
    line = normalize(re.sub('\n', '', line))
    res = l.classify(line)
    #f.write('++++ \t'+str(line)+'\n')
    ll = str(line)+'\t'+str(res)+'\n'
    print '-->',ll
    if len(res) > 2:
      if (res[0][1] == 'EN') or (res[1][1] == 'EN') or (res[2][1] == 'EN'):
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
          lang = l.classify(w1)
          vLangs.append([w1,lang])

          if len(lang) > 0:
            if lang[0][1] in dLangs:
              dLangs[lang[0][1]] += 1
            else:
              dLangs[lang[0][1]] = 1

          print [w1,lang],line,vLine
          print "------------"



          vLine.pop(0)

      
        if len(vLine) > 0:
          w1 = ''
          for w in vLine:
            w1 = w1+' '+w
          if len(w1) > 2:  
            w1 = w1[1:] #remove first char

            lang = l.classify(w1)
            vLangs.append([w1,lang])
            if len(lang) > 0:
              if lang[0][1] in dLangs:
                dLangs[lang[0][1]] += 1
              else:
                dLangs[lang[0][1]] = 1

            print [w1,lang],line,vLine
            print "------------"

        print dLangs
        print "zzzzzzzzzzzzzzzzzzzzzzz"
    #f.write("======================\n")
  fd.close()

if __name__ == '__main__':
  l = LangId()
  f = open('./r2.txt', 'w')
  fd = open('./aren2.txt', 'r')
  testWindow3Words(fd,f)
  #test3(fd,f)
  fd.close()
  '''
  
  print '=================='
  fd = open('./esen.txt', 'r')
  test3(fd,f)
  fd.close()
  print '=================='
  fd = open('./es.txt', 'r')
  test(fd,f)
  fd.close()
  '''
  f.close()