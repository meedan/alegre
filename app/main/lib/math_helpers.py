import math
import numpy as np
import scipy

def cosine_sim(vecA, vecB):
  """
  Return the cosine simularity between two vectors vecA and vecB.
  @return integer between zero and one inclusive. One indicates identicial
  """
  csim = np.dot(vecA, vecB) / (np.linalg.norm(vecA) * np.linalg.norm(vecB))
  if np.isnan(np.sum(csim)):
    return 0
  return csim

def angular_similarity(vecA, vecB):
  """
  Return the angular simularity between two vectors vecA and vecB.
  @return integer between zero and one inclusive. One indicates identicial
  """
  #Ensure cosine is between zero and one
  cosdist=max(0,min(scipy.spatial.distance.cosine(vecA,vecB),1))
  return 1-math.acos(1-cosdist)/math.pi
