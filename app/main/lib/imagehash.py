from PIL import Image, ImageDraw, ImageFilter, ImageOps
import imagehash
import struct
import numpy as np

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
