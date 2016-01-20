import os
import codecs
import time
from datetime import datetime

class Train:

    def __init__(self, root=''):

        # Setting root directory for training data
        if root:
            self.root = root
            self.using_builtin_training = False
        else:
            #self.root = 'corpora/corpus-esaren'
            self.root = __file__.rsplit('/',2)[0] + '/corpus-esaren'
            self.using_builtin_training = True
        print self.root
        self.root_depth = len(self.root.split('/'))

        # Set of languages
        self.lang_set = set()

        # Temp Training Samples
        # These are sample adding in run-time
        # self.temp_train_data = {
        #   'en': ['hello world', 'this is sparta'],
        #   'es': ['hasta la vista', 'hola amigos']
        # }
        self.temp_train_data = {}
           
    def get_corpus(self):
        self.corpus = []
        self.load()
        return self.corpus

    def get_corpus_path(self):
        return self.root

    def get_lang_set(self):
        return list(self.lang_set)

    def addModel(self, text=u'', lang=''): #CLARISSA
	if not text or not lang:
            raise Exception("Error: No input text given!")
        if not lang in self.temp_train_data:
            self.temp_train_data[lang] = [text]
        else:
            self.temp_train_data[lang].append(text)


    def add(self, text=u'', lang=''):
        if self.using_builtin_training:
            print "Warning: Cannot add training samples to builtin training-set."
            return
        elif not text or not lang:
            raise Exception("Error: No input text given!")
        if not lang in self.temp_train_data:
            self.temp_train_data[lang] = [text]
        else:
            self.temp_train_data[lang].append(text)

    def save(self, domain='', filename=''):
        
        if self.using_builtin_training:
            raise Exception("Failed to save data, use custom training-set instead.")
        
        if not domain:
            timestamp = datetime.now().strftime("%y%m%d%H%M%S")
            folder_path = self.root + '/batchTS' + timestamp
        else:
            folder_path = self.root + '/' + domain
        
        try:
            os.mkdir(folder_path)
        except:
            pass  
        
        for lang in self.temp_train_data:
            
            lang_folder_path = folder_path + '/' + lang
            
            try:
                os.mkdir(lang_folder_path)
            except:
                pass
            
            if not filename:
                filename_and_path = lang_folder_path + '/file.txt'
            else:
                filename_and_path = lang_folder_path + '/' + filename
            
            f = codecs.open(filename_and_path, mode='w', encoding='utf-8')
            for sample in self.temp_train_data[lang]:
                text = sample + u'\n'
                f.write(text)
            
            f.close()

    def get_last_modified(self):
        # Get corpus last modified timestamp
        if self.using_builtin_training:
            return 0
        else:
            return os.path.getmtime(self.root)

    def visit(self, arg, dirname, names):
        #print dirname
        path = dirname.split('/')
        #print 'path:', path, len(path)

        if len(path) == self.root_depth + 2:
            lang = path[-1]

            # Update Language Set
            self.lang_set.add(lang)

            # Ignore hidden files
            names = [name for name in names if not name.startswith('.')]

            for name in names:
                self.corpus.append((lang, dirname + '/' + name)) 
                #print lang, path, dirname + '/' + name

    def load(self):
        os.path.walk(self.root, self.visit, '') 
