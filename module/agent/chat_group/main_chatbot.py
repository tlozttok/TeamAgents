from ...ai_api.LLM import chat
from typing import List,Literal,Dict

class MainChatBot:
  def __init__(self,entity:chat.ChatEntity,model:Literal["gpt3.5","gpt4","glm3","glm4","glm4v"]|None=None):
    self.mainEntity = entity
    self.model_setting=model if model else "glm3"
    self.img_url_cache=[]
    
  def single_chat(self,text:str, model:Literal["gpt3.5","gpt4","glm3","glm4","glm4v"]|None=None):
    if model:
      self.model_setting=model
    
    return self.mainEntity(text,self.model_setting,self.img_url_cache)

  def add_img_to_next_chat(self,img_url:str):
    self.img_url_cache.append(img_url)