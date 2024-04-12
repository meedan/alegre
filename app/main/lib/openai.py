import pickle
from flask import current_app as app
import openai.embeddings_utils
import hashlib
from app.main.lib import redis

PREFIX_OPENAI = "openai-"
EMBEDDING_CACHE_DEFAULT = 60*60*24*7 #7 days (value is in seconds)
def retrieve_openai_embeddings(text, model_key):
    """Return the vector embeddings of text using OpenAI API """
    r_cache = redis.get_client()
    text = text.strip()
    textmd5 = hashlib.md5(text.encode('utf-8')).hexdigest()
    key = f"cache_{model_key}_{textmd5}"
    val_from_cache = r_cache.get(key)
    if val_from_cache is not None:
        return pickle.loads(val_from_cache)
    openai.api_key = app.config['OPENAI_API_KEY']
    app.logger.info(f"Calling OpenAI API")
    model_key_without_openai_prefix = model_key[len(PREFIX_OPENAI):]
    try:
        embeddings = openai.embeddings_utils.get_embedding(text, engine=model_key_without_openai_prefix)
        r_cache.set(key, pickle.dumps(embeddings))
        r_cache.expire(key, EMBEDDING_CACHE_DEFAULT)
    except Exception as caught_exception:
        app.logger.error(f"Unable to retreieve OpenAI embeddings. Error was {caught_exception}")
        embeddings = None
    return embeddings
