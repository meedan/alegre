# Do you speak London?

For fetting a sentence language:

`$ python dysl.py --model ./dysl/corpora/multiLanguage/trainedCorpus2.obj  Can you tell if this is in English?`

For creating a new model it is necessary to inform the file where the model will be recorded and training the corpus path:

```
	$ python dysl.py --train  ./dysl/corpora/test/testModel.obj --corpus /home/ccx/work/dysl/dysl/corpora/test
```

/corpora/multiLanguage/TrainedCorpus2.obj comes pre-trained on 97 languages (ISO 639-1 codes given):

    gu - ga - gl - lb - la - lo - tr - lv - lt - th - te - ta - de - da - dz - qu - kn - el - eo - en - zh - eu - zu - es - ru - rw - ro - jv - be - bg - ms - wa - bn - br - bs - ja - oc - or - xh - ca - cy - cs - ps - pt - tl - pa - pl - hy - hr - ht - hu - hi - vo - he - mg - ml - mn - mk - ur - mt - uk - mr - ug - af - vi - is - am - it - an - as - ar - et - az - id - nl - nn - no - nb - ne - fr - fa - fi - fo - ka - kk - sr - sq - ko - sv - km - sk - si - ku - sl - ky - sw - se 

To add a new sentence in a existing model file:

`$ python dysl.py --model ./dysl/corpora/test/testModel.obj --lang "en" "new sentence"`


To list the languages inside a model file:

`$ python dysl.py --listLanguages ./dysl/corpora/multiLanguage/trainedCorpus2.obj`


For listing of all CLI options:

`$ python dysl.py --help`

## Use in Code

You can also use dysl's LangID within your code

```python
from dysl.langid import LangID

filename ='/home/ccx/work/dysl/dysl/corpora/multiLanguage/trainedCorpus2.obj'
l = LangID(unk=unk)
l.trainPRELOAD(filename=args.model)
lang = l.classify(“input text”)
print 'Input text:', input_text
print 'Language:', lang
```

## DYSL REST API design

A REST API for DYSL

### Current features

* Add training sample to a model file
* List supported languages
* Language Identification


#### Add training sample to a model file

Format: POST /api/sample

`curl -X POST http://localhost:3000/api/sample -d '{"sentence":"this is a new sample","language":"en"}' -H "Content-Type: application/json"`

Returns:

`{"type":"success"}`

In order to use this method, you need to have the corpus files inside the API server.

#### List supported languages in a model

Format: GET /api/language

`curl -X GET http://localhost:3000/api/language -H "Content-Type: application/json" -H 

Returns:

`{ "type": "language_code", "data": ["en","pt","es","ar"]}`


#### Language Identification

Format: GET /api/identification

`curl -X GET http://localhost:3000/api/identification -d '{"sentence":"what is my language?"}' -H "Content-Type: application/json" 

Returns:

`{ "type": "language", "data": " [ { "name": "en", "probability": "0.8" },{ "name": "ar", "probability": "0.1" }, { "name": "pt", "probability": "0.1" }]"}`


