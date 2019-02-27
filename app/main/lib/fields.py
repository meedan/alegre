from flask_restplus import fields

class JsonObject(fields.Raw):
    __schema_type__ = ["object"]
    __schema_example__ = "json object"
