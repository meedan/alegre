from PIL import Image
import imagehash
import struct
import json
import hashlib
import numpy as np
import io

from sqlalchemy import text
from pdqhashing.hasher.pdq_hasher import PDQHasher

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
  return imagehash.average_hash(ensure_pil(im))
def compute_phash(im):
  """Compute perceptual hash using ImageHash library
    :param im: Numpy.ndarray
    :returns: Imagehash.ImageHash
  """
  return imagehash.phash(ensure_pil(im))

def compute_pdq(iobytes):
  """Compute perceptual hash using ImageHash library
    :param im: Numpy.ndarray
    :returns: Imagehash.ImageHash
  """
  #hash_vector, quality = pdqhash.compute(ensure_pil(im))
  #print(type(hash_vector))
  #print(hash_vector)
  #return hash_vector.ravel().tolist()
  pdq_hasher = PDQHasher()
  hash_and_qual = pdq_hasher.fromBufferedImage(iobytes)
  #hash_array =  imagehash.hex_to_hash(hash_and_qual.getHash().toHexString())
  #return  hash_array.hash.ravel().tolist()
  return hash_and_qual.getHash().dumpBitsFlat() #This is a string of 0's and 1's
  
# def pdq(filename):
#     try:
#         hash_and_qual=pdq_hasher.fromFile(filename)
#         return imagehash.hex_to_hash(hash_and_qual.getHash().toHexString())
#     except Exception as e:
#         print(f"{filename}: {e}")
#         return None
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
