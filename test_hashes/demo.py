from tmkfile import TMKFile
from scipy.spatial import distance
import sys
from itertools import combinations
import os

#Goal reproduce level-1 hash distances reported at 
#	https://github.com/meedan/alegre/tree/develop/threatexchange/tmk#look-at-all-pair-scores

#Namely
"""
$ ./tmk-two-level-score --c1 -1.0 --c2 0.0 *.tmk | sort -n
-0.310042 0.017566 doorknob-hd-no-bar.tmk pattern-sd-with-large-logo-bar.tmk
-0.088088 0.033167 chair-19-sd-bar.tmk pattern-sd-with-large-logo-bar.tmk
-0.083061 0.033179 chair-20-sd-bar.tmk pattern-sd-with-large-logo-bar.tmk
-0.077388 0.026434 chair-22-with-small-logo-bar.tmk pattern-sd-with-small-logo-bar.tmk
-0.074581 0.021536 chair-22-with-small-logo-bar.tmk pattern-sd-with-large-logo-bar.tmk
-0.071327 0.021766 chair-22-sd-grey-bar.tmk pattern-sd-with-large-logo-bar.tmk
-0.070220 0.022146 chair-orig-22-sd-bar.tmk pattern-sd-with-large-logo-bar.tmk
-0.069683 0.019660 chair-22-sd-sepia-bar.tmk pattern-sd-with-large-logo-bar.tmk
-0.067127 0.025258 chair-22-sd-sepia-bar.tmk pattern-sd-with-small-logo-bar.tmk
-0.066280 0.023696 chair-orig-22-hd-no-bar.tmk pattern-sd-with-small-logo-bar.tmk
-0.066129 0.028783 chair-20-sd-bar.tmk pattern-sd-with-small-logo-bar.tmk
-0.064803 0.023406 chair-orig-22-fhd-no-bar.tmk pattern-sd-with-small-logo-bar.tmk
-0.063257 0.025060 chair-22-sd-grey-bar.tmk pattern-sd-with-small-logo-bar.tmk
-0.063251 0.019399 chair-orig-22-hd-no-bar.tmk pattern-sd-grey-bar.tmk
-0.061950 0.019116 chair-orig-22-fhd-no-bar.tmk pattern-sd-grey-bar.tmk
-0.061946 0.025864 chair-19-sd-bar.tmk pattern-sd-with-small-logo-bar.tmk
...
0.919339 0.921573 chair-20-sd-bar.tmk chair-22-with-small-logo-bar.tmk
0.926403 0.953071 chair-22-with-small-logo-bar.tmk chair-orig-22-sd-bar.tmk
0.926929 0.953268 chair-22-sd-grey-bar.tmk chair-22-with-small-logo-bar.tmk
0.927289 0.953265 chair-22-sd-sepia-bar.tmk chair-22-with-small-logo-bar.tmk
0.952329 0.961902 chair-19-sd-bar.tmk chair-orig-22-sd-bar.tmk
0.952936 0.962041 chair-19-sd-bar.tmk chair-22-sd-sepia-bar.tmk
0.953346 0.962158 chair-19-sd-bar.tmk chair-22-sd-grey-bar.tmk
0.981078 0.954990 pattern-hd-no-bar.tmk pattern-longer-no-bar.tmk
0.985408 0.988313 chair-20-sd-bar.tmk chair-orig-22-sd-bar.tmk
0.985554 0.988220 chair-20-sd-bar.tmk chair-22-sd-sepia-bar.tmk
0.985930 0.988437 chair-20-sd-bar.tmk chair-22-sd-grey-bar.tmk
0.989083 0.991138 chair-19-sd-bar.tmk chair-20-sd-bar.tmk
0.999750 0.999720 chair-22-sd-sepia-bar.tmk chair-orig-22-sd-bar.tmk
0.999779 0.999763 chair-22-sd-grey-bar.tmk chair-22-sd-sepia-bar.tmk
0.999883 0.999877 chair-orig-22-fhd-no-bar.tmk chair-orig-22-hd-no-bar.tmk
0.999963 0.999964 chair-22-sd-grey-bar.tmk chair-orig-22-sd-bar.tmk
"""

def tmklevel1(file1,file2):
	return 1-distance.cosine(file1.pure_average_feature,file2.pure_average_feature)

if __name__=="__main__":
	files=[]
	for file in sys.argv[1:]:
		files.append(TMKFile(file))
	
	combos=combinations(files,2)
	for a,b in combos:
		print(tmklevel1(a,b),os.path.basename(a.filename),os.path.basename(b.filename))

