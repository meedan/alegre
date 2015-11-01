import sys
from argparse import ArgumentParser
from dysl.utils import decode_input
from dysl.langid import LangID


config = {
	'modelFile' : ''}

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

#python dysl.py --model ./dysl/corpora/multiLanguage/trainedCorpus2.obj  Can you tell if this is in English?
#python dysl.py --identification  Can you tell if this is in English?
def main():

    load_config(filename='./config.yml', debug=False)

    parser = ArgumentParser(description='Do you speak London? A library for Natural Language Identification.')
    parser.add_argument('--list-langs', action='store_true', help='List supported languages in training data')
    parser.add_argument('--unk', choices=['y','n'], default='n', help='Input text to classify')
    parser.add_argument('--corpus', default='', help='Specify path to custom training-set')
    parser.add_argument('--lang', help='Add training sample for the language specified. Requires model file and sentence. Ex: $ python dysl.py --model ./dysl/corpora/multiLanguage/trainedCorpus2.obj --lang "en" "new training sentence"' )
    ## CLARISSA - create preload training file
    parser.add_argument('--train', default='', help='create preload training model file')
    ## CLARISSA - preload training file
    parser.add_argument('--model', default='', help='preloaded training model file')
    #### CLARISSA 
    parser.add_argument('--listLanguages', default='', help='list languages inside a model file.Example: python dysl.py --listLanguages ./dysl/corpora/test/testModel.obj')
    #### CLARISSA Identification API function
    parser.add_argument('--identification', nargs='*', help='Language Identification')

    parser.add_argument('input', nargs='*', help='Input text to classify')


    args = parser.parse_args()

    unk = False if args.unk == 'n' else True

    input_text = decode_input(args.input)

    if args.list_langs:
        l = LangID(unk=unk)
        l.train(root=args.corpus)
        print 'Languages: [' + '-'.join(l.get_lang_set()) + ']'
        sys.exit()
    elif args.identification:
        l = LangID(unk=unk)
        l.trainPRELOAD(filename=config['modelFile'])
	input_text = decode_input(args.identification)
	langs = l.classifyReturnAll(input_text,config['stopwordsPath']) 
        print 'Input text:', input_text
        print 'Languages:', langs
    elif args.train and args.corpus:
        l = LangID(unk=unk)
        l.trainORIGINAL(root=args.corpus,filename=args.train)
    elif args.lang and args.model and input_text:
        l = LangID(unk=unk)
        #l.train(root=args.corpus) - OLD
        l.trainPRELOAD(filename=args.model)
        #l.add_training_sample(args.model, text=input_text, lang=args.lang)
        l.save_training_samples("",args.model, text=input_text, lang=args.lang)
        sys.exit('Training Sample for "%s" added successfully.\n' % args.lang)
    elif input_text and args.model:
        l = LangID(unk=unk)
        l.trainPRELOAD(filename=args.model)
        lang = l.classify(input_text)
        print 'Input text:', input_text
        print 'Language:', lang
    elif args.listLanguages:
        l = LangID(unk=unk)
        l.trainPRELOAD(filename=args.listLanguages)
	print l.listLanguages()
    else:
        parser.print_help()
        sys.exit('\n')

if __name__ == '__main__':
    main()
    '''
    try:
        main()
    except Exception, e:
        print "Failed to run!"
        print e
    '''
