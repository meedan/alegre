def decode_input(text_in):
    """ Decodes `text_in`
        If text_in is is a string, 
        then decode it as utf-8 string.
        If text_in is is a list of strings,
        then decode each string of it, 
        then combine them into one outpust string.  
    """
    
    if type(text_in) == list:
        text_out = u' '.join([t.decode('utf-8') for t in text_in])
    else:
        text_out = text_in.decode('utf-8')
    return text_out

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
