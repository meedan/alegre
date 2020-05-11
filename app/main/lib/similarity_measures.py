import math
import numpy as np
from scipy.spatial.distance import cosine

def cosine_similarity(vecA, vecB):
  """
  Return the cosine simularity between two vectors vecA and vecB.
  @return float between 0 and 1 inclusive. One indicates identical.
  """
  csim = np.dot(vecA, vecB) / (np.linalg.norm(vecA) * np.linalg.norm(vecB))
  if np.isnan(np.sum(csim)):
    return 0
  return csim

def angular_similarity(vecA, vecB):
  """
  Return the angular simularity between two vectors vecA and vecB.
  @return float between 0 and 1 inclusive. One indicates identical.
  """
  # Ensure cosine is between zero and one
  cosdist = max(0, min(cosine(vecA, vecB), 1))
  return 1 - math.acos(1 - cosdist) / math.pi
