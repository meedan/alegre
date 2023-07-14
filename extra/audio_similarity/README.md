# Perl and Python audio fingerprint scorers

Reference implementations for Alegre's code.

Example fingerprints are given in ex1.json, ex2.json, and ex3.json

ex1 and ex2 should match. ex3 should match itself but not match the others.

The Perl and Python scripts expect arguments via commandline. Envoke as
```
cat ex1.json ex2.json | xargs perl perl_scorer.pl
cat ex1.json ex3.json | xargs perl perl_scorer.pl
cat ex3.json ex3.json | xargs perl perl_scorer.pl

cat ex1.json ex2.json | xargs python python_scorer.py
cat ex1.json ex3.json | xargs python python_scorer.py
cat ex3.json ex3.json | xargs python python_scorer.py
```

Output for these commands are:
```
0.998585972850679
0
1
0.9985859728506787
0
1.0
```

Note the functions return **similarity** (one is a perfect match).