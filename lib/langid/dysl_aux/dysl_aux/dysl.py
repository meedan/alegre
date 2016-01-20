import sys
import codecs

#from dyslib.lm import LM
from social import SocialLM as LM


corpora = {
    'English': 'corpora/corpus-5langs/en.txt',
    'Spanish': 'corpora/corpus-5langs/es.txt',
    'French': 'corpora/corpus-5langs/fr.txt',
    'Arabic': 'corpora/corpus-5langs/ar.txt',
    'Arabizi': 'corpora/corpus-5langs/ar-latin.txt',
}


def readfile(filename):
    #print 'readfile', filename
    f = codecs.open(filename, encoding='utf-8')
    tokenz = LM.tokenize(f.read())
    f.close()
    #print tokenz
    return tokenz

def main_cli():
    
    ngram = 3
    lrpad = u' '
    verbose=True
    #corpus_mix='l'
    corpus_mix=0

    lm = LM(n=ngram, verbose=verbose, lpad=lrpad, rpad=lrpad, 
            smoothing='Laplace', laplace_gama=0.1, 
            corpus_mix=corpus_mix)

    for lang in corpora:
        print 'Training on language,', lang
        lm.add_doc(doc_id=lang, doc_terms=readfile(corpora[lang]))

    intxt = u''
    for u in sys.argv[1:]:
        intxt = intxt + u.decode('utf-8')
    
    #print term2ch(intxt)
    result = lm.calculate(doc_terms=term2ch(intxt))
    #print result['calc_id']
    print result

def main_esaren():

    ngram = 3
    lrpad = u' '
    verbose=False
    corpus_mix='l'

    lm = LM(n=ngram, verbose=verbose, lpad=lrpad, rpad=lrpad, 
            smoothing='Laplace', laplace_gama=0.1, 
            corpus_mix=corpus_mix)

    from corpora.corpuslib import Train, Test, Accuracy
    #train = corpuslib.Train()
    train = Train()
    corpus = train.get_corpus()

    for item in corpus:
        lm.add_doc(doc_id=item[0], doc_terms=readfile(item[1]))

    #a = corpuslib.Accuracy()
    #t = corpuslib.Test(root='', langid=lm, accuracy=a)
    a = Accuracy()
    t = Test(root='', langid=lm, accuracy=a)
    t.open_logfile()
    t.start()
    t.close_logfile()
    a.evaluate()


if __name__ == '__main__':

    PROFILING = False

    if PROFILING:
        import cProfile
        import pstats

    # For an interactive mode
    #main_cli()

    # For training and testing esaren corpus
    if PROFILING:
        cProfile.run('main_esaren()','train_prof')
        p_stats = pstats.Stats('train_prof')
        p_stats.sort_stats('time').print_stats(10)
    else:
        main_esaren()
        pass

