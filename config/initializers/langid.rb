MODEL_PATH = CONFIG['langid'] + '/models/'
STOPWORDS_PATH = CONFIG['langid'] + '/stopwords/'
MODEL_SENTENCES = CONFIG['langid'] + '/modelSentences/'
LANGUAGES = ['AR', 'EN', 'FA', 'HI', 'IT', 'PT', 'TL', 'AZ', 'ES', 'FR', 'ID', 'KA', 'RU', 'TR','ZH-CHS','ZH-CHT']

Alegre::LangId.new.start
