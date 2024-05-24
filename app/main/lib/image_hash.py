import hashlib

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
