import copy
import hashlib
from sqlalchemy.dialects.postgresql import JSONB

from app.main import db
from app.main.lib.image_hash import compute_phash_int, sha256_stream

def make_hash(o):
    """
    Makes a hash from a dictionary, list, tuple or set to any level, that contains
    only other hashable types (including any lists, tuples, sets, and
    dictionaries).
    """
    m = hashlib.md5()
    if isinstance(o, (set, tuple, list)):
        return tuple([make_hash(e) for e in o])    
    elif not isinstance(o, dict):
        return hash(o)
    new_o = copy.deepcopy(o)
    for k, v in new_o.items():
        new_o[k] = make_hash(v)
    m.update(str(hash(tuple(frozenset(sorted(new_o.items()))))).encode())
    return m.hexdigest()

class ContextHash(db.Model):
    """ Model for storing context details """
    __tablename__ = 'context_hashes'

    id = db.Column(db.Integer, primary_key=True)
    hash_key = db.Column(db.String(64, convert_unicode=True), nullable=False, index=True)
    context = db.Column(JSONB(), default=[], nullable=False)
    __table_args__ = (
        db.Index('ix_context_hashes_context', context, postgresql_using='gin'),
    )

    @staticmethod
    def from_context(context):
        hash_key = make_hash(context)
        existing = ContextHash.query.filter(ContextHash.hash_key==hash_key).first()
        if existing:
            return existing
        else:
            context = ContextHash(hash_key=hash_key, context=context)
            db.session.add(context)
            db.session.commit()
            return context
