# Demo

## Data

Ensure you have the `sample-hashes` folder of TMK files from
https://github.com/facebook/ThreatExchange/tree/master/tmk/sample-hashes

## Execute

Then you can run
`python demo.py sample-hashes/*.tmk`

## Output

The output will be a TMK level-1 score and the two filenames for that score.
The output will match the first score and file names when running the C++ version; namely
`./tmk-two-level-score --c1 -1.0 --c2 0.0 sample-hashes/*.tmk`

The TMK level-2 score is **not** present.

## Impact

We can:
1. Read .tmk files
2. Store the `pure_average_feature` vector from a tmk file into a separate datastore such as Elasticsearch
3. Query those vectors and only select vectors with a score >0.7 to compute TMK level-2 hashes (where we need to invoke the C++ binaries).


## Detail

First 10 lines of output
```
0.989083147276229 chair-19-sd-bar.tmk chair-20-sd-bar.tmk
0.9533471719622231 chair-19-sd-bar.tmk chair-22-sd-grey-bar.tmk
0.9529366913025642 chair-19-sd-bar.tmk chair-22-sd-sepia-bar.tmk
0.434536555713968 chair-19-sd-bar.tmk chair-22-with-large-logo-bar.tmk
0.8953929141414919 chair-19-sd-bar.tmk chair-22-with-small-logo-bar.tmk
0.7278669892886565 chair-19-sd-bar.tmk chair-orig-22-fhd-no-bar.tmk
0.7278327109609791 chair-19-sd-bar.tmk chair-orig-22-hd-no-bar.tmk
0.9523292208630433 chair-19-sd-bar.tmk chair-orig-22-sd-bar.tmk
0.1993264834495001 chair-19-sd-bar.tmk doorknob-hd-no-bar.tmk
-0.013393060454754968 chair-19-sd-bar.tmk pattern-hd-no-bar.tmk
```
