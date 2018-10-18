from flask import request
from flask_restplus import Resource, Namespace, fields
import spacy

api = Namespace('spacy', description='spaCy operations')
spacy_request = api.model('spacy_request', {
    'text': fields.String(required=True, description='text to identify'),
    'model': fields.String(required=True, description='language model to use')
})

@api.route('/')
class SpacyResource(Resource):
    @api.response(200, 'spaCy successfully queried.')
    @api.doc('Make a spaCy query')
    @api.expect(spacy_request, validate=True)
    def post(self):
        nlp = spacy.load(request.json['model'])
        doc = nlp(request.json['text'])
        words = [{'text': w.text, 'tag': w.tag_} for w in doc]
        ents = [
            {
                'start': ent.start_char,
                'end': ent.end_char,
                'type': ent.label_,
                'text': str(ent)
            } for ent in doc.ents
        ]
        return {'words': words, 'entities': ents}
