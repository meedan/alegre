import os
import math
import numpy as np
import scipy
def similarity_for_model_name(language_model_name, vecA, vecB):
  if not language_model_name:
    language_model_name = os.getenv('MODEL_NAME')
  if language_model_name == "WordVec":
    return cosine_sim(vecA, vecB)
  elif language_model_name == "UniversalSentenceEncoder":
    return angular_similarity(vecA, vecB)
  else:
    raise ValueError("No similarity metric implemented for provided language model!")

def similarity_for_model(language_model, vecA, vecB):
  return similarity_for_model_name(language_model.model_name(), vecA, vecB)

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
