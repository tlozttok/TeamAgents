from ..Client.client import main_client
import numpy as np


class Embedding:
  def __init__(self):
    self.client = main_client
    
  def get_embedding(self, text, model):
    embedding=main_client.embedding(model=model, input=text, encoding_format="float", dimensions=1024)
    return embedding.data[0].embedding
  
  def cosine_similarity(self, embedding1, embedding2):
    e1=np.array(embedding1)
    e2=np.array(embedding2)
    return np.dot(e1, e2)/(np.linalg.norm(e1)*np.linalg.norm(e2))
    