from PIL import Image, ImageDraw, ImageFilter, ImageOps
import imagehash
import struct
import json
import hashlib
import numpy as np
from sqlalchemy import text

def ensure_pil(im):
  """Ensure image is Pillow format"""
  try:
    im.verify()
    return im
  except:
    return Image.fromarray(im.astype('uint8'), 'RGB')

def compute_ahash(im):
  """Compute average hash using ImageHash library
    :param im: Numpy.ndarray
    :returns: Imagehash.ImageHash
  """
  return imagehash.average_hash(ensure_pil(im_pil))

def compute_phash(im):
  """Compute perceptual hash using ImageHash library
    :param im: Numpy.ndarray
    :returns: Imagehash.ImageHash
  """
  return imagehash.phash(ensure_pil(im))

def phash2int(phash):
  """Compute perceptual hash using ImageHash library and convert to binary
    :param phash: Imagehash.ImageHash
    :returns: binary-encoded bigint
  """
  phash.hash[-1] = False
  phash_as_bigint = struct.unpack('Q', np.packbits(phash.hash))[0]
  return phash_as_bigint

def compute_phash_int(im):
  """Compute perceptual hash using ImageHash library and convert to binary
    :param im: Numpy.ndarray
    :returns: binary-encoded bigint
  """
  return phash2int(compute_phash(im))

def compute_dhash(im):
  """Compute difference hash using ImageHash library
    :param im: Numpy.ndarray
    :returns: Imagehash.ImageHash
  """
  return imagehash.dhash(ensure_pil(im))

def compute_whash(im):
  """Compute wavelet hash using ImageHash library
    :param im: Numpy.ndarray
    :returns: Imagehash.ImageHash
  """
  return imagehash.whash(ensure_pil(im))

def compute_whash_b64(im):
  """Compute wavelest hash base64 using ImageHash library
    :param im: Numpy.ndarray
    :returns: Imagehash.ImageHash
  """
  return lambda im: imagehash.whash(ensure_pil(im), mode='db4')

def search_by_phash(session, phash, threshold=6, limit=1, offset=0, filter={}):
  cmd = """
    SELECT * FROM (
      SELECT images.*, BIT_COUNT(phash # :phash)
      AS hamming_distance FROM images
    ) f
    WHERE hamming_distance < :threshold
    AND context @> (:filter)::jsonb
    ORDER BY hamming_distance ASC
    LIMIT :limit
    OFFSET :offset
  """
  matches = session.execute(text(cmd), {
    'phash': phash,
    'threshold': threshold,
    'limit': limit,
    'offset': offset,
    'filter': json.dumps(filter)
  }).fetchall()
  keys = ('id', 'sha256', 'phash', 'ext', 'url', 'context', 'score')
  results = [ dict(zip(keys, values)) for values in matches ]
  return results

def sha256_stream(stream, block_size=65536):
  """Generates SHA256 hash for a file stream (from Flask)
  :param fp_in: (FileStream) stream object
  :param block_size: (int) byte size of block
  :returns: (str) hash
  """
  sha256 = hashlib.sha256()
  for block in iter(lambda: stream.read(block_size), b''):
    sha256.update(block)
  return sha256.hexdigest()
