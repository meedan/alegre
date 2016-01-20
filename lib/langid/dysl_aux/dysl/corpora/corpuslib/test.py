import os
import codecs

class Test:

    def __init__(self, root='', langid=None, accuracy=None):

        #print 'Testing'
        if root:
            self.root = root
        else:
            #self.root = 'corpora/corpus-esaren.test'
            self.root = __file__.rsplit('/',2)[0] + '/corpus-esaren.test'
        #print self.root
        self.root_depth = len(self.root.split('/')) 

        self.langid = langid
        self.a = accuracy

    def visit(self, arg, dirname, names):
        #print dirname
        path = dirname.split('/')
        #print 'path:', path, len(path), self.root_depth

        if len(path) == self.root_depth:
            #print names
            for i in range(len(names)-1,0,-1):
                if names[i].startswith('.'):
                    del names[i]
            #print names
        else:
            lang = path[-1]
            #print arg, dirname, names
            names = [name for name in names if not name.startswith('.')]
            for name in names:
                filename = dirname + '/' + name
                #print 'filename:', filename
                fd = codecs.open(filename, encoding='utf-8')
                lines = fd.read().split('\n')
                for line in lines:
                    #print '=>', line
                    line = self.langid.normalize(line)
                    #print ':', line
                    res = self.langid.classify(line)
                    #print lang, ':', res
                    karbasa = res[1]
                    if karbasa < 0.05:
                        detected_lang = 'unk'
                    else:
                        detected_lang = res[0]
                    if lang == detected_lang:
                        self.a.update(correct=True)
                    else:
                        if False:
                            print 'incorrect:'
                            print ' ', lang, 'detected as', detected_lang
                            #print ' ', line
                            print ' ', res 
                        self.a.update(correct=False)
                    self.add_log(lang, detected_lang, karbasa, line)
                fd.close()

    def start(self):
        os.path.walk(self.root, self.visit, '')    

    def open_logfile(self, logfile_name='logs.csv'):
        #self.logfd = open(logfile_name,'w')
        self.logfd = codecs.open(logfile_name, encoding='utf-8', mode='w')
        #self.logfd.write('What, ')

    def close_logfile(self):
        self.logfd.close()

    def add_log(self, lang='', detected_lang='', karbasa=0, line=''):
        if lang == detected_lang:
            what = 'correct'
        else:
            what = 'incorrect'
        what_txt = lang + '=>' + detected_lang
        #print type(result[1]['all_probs']), result[1]['all_probs']
        #result[1]['all_probs'].sort()
        #probs = ','.join(map(str,result[1]['all_probs']))
        #seenunseen = ','.join(map(str,result[1]['seen_unseen_count']))
        #log_line = what + ',' + probs + ',' + seenunseen + ',' + what_txt + '\n'
        log_line = what + ',' + str(karbasa) + ',' + what_txt + ',' + line.replace(',','') + '\n'
        self.logfd.write(log_line)



class Accuracy:

    def __init__(self):
        self.correct = 0
        self.incorrect = 0

    def update(self, correct=True):
        if correct:
            self.correct += 1
        else:
            self.incorrect += 1
        #print 'updates', self.correct, self.incorrect

    def evaluate(self):
        total_cases = self.correct + self.incorrect
        accuracy = self.correct * 100.0 / total_cases
        print 'Accuracy = %f %% (%d of %d test cases)' % (accuracy, self.correct, total_cases)

