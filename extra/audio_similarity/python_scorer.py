import numpy as np
import sys
import json

def correlation(listx, listy):
    if len(listx) == 0 or len(listy) == 0:
        # Error checking in main program should prevent us from ever being
        # able to get here.
        raise Exception('Empty lists cannot be correlated.')
    if len(listx) > len(listy):
        listx = listx[:len(listy)]
    elif len(listx) < len(listy):
        listy = listy[:len(listx)]
    covariance = 0
    for i in range(len(listx)):
        bits=bin(((1 << 32) - 1) & (listx[i] ^ listy[i])) #Ref: https://stackoverflow.com/a/28383647
        #print(listx[i],listy[i],bits.count("1"))
        covariance += 32 - bits.count("1") #SAH: Does this assume 32-bit floats?
    covariance = covariance / float(len(listx))
    return covariance/32
  
# return cross correlation, with listy offset from listx
def cross_correlation(listx, listy, offset, min_overlap):
    if offset > 0:
        listx = listx[offset:]
        listy = listy[:len(listx)]
    elif offset < 0:
        offset = -offset
        listy = listy[offset:]
        listx = listx[:len(listy)]
    if min(len(listx), len(listy)) < min_overlap:
        # Error checking in main program should prevent us from ever being
        # able to get here.
        return 
    #raise Exception('Overlap too small: %i' % min(len(listx), len(listy)))
    return correlation(listx, listy)
  
# cross correlate listx and listy with offsets from -span to span
def compare(listx, listy, span, step):
    if span > min(len(listx), len(listy)):
        span = min(len(listx), len(listy)) -1
    min_overlap = span
    corr_xy = []
    for offset in np.arange(-span, span + 1, step):
        #print(offset);
        corr_xy.append(cross_correlation(listx, listy, offset, min_overlap))
    return corr_xy
  
# return index of maximum value in list
def max_index(listx):
    max_index = 0
    max_value = listx[0]
    for i, value in enumerate(listx):
#        if value and max_value and value > max_value: #SAH: This is wrong!
        if max_value==None or (value and value > max_value):
            max_value = value
            max_index = i
    return max_index
  
def get_max_corr(corr, source, target, span, step):
    max_corr_index = max_index(corr)
    #max_corr_offset = -span + max_corr_index * step #This is not used.
    return corr[max_corr_index]

def get_score(first, second, span=150, step=1):
    if len(first) > 0 and len(second) > 0 and len(first)*0.8 <= len(second) and len(first)*1.2>=len(second):
       corr = compare(first, second, span, step)
       return get_max_corr(corr, first, second, span, step)
    return 0

listx = json.loads(sys.argv[1])
listy = json.loads(sys.argv[2])
#listx=[1,2,3,4,5,6]*10 + [30,40,50,60,70,80]*5;
#listy=[30,40,50,60,70,80]*5;
#listx=[1,2,3,4,5,6,7,8,9];
#listy=[4,5,6];
#print(get_score(listx,listy))
#print(correlation(listx,listy))

#for offset in range(-2,3,1):
#	print(cross_correlation(listx,listy,offset))
#print(compare(listx,listy,150,1));
print(get_score(listx,listy))



