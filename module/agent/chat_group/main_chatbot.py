from ...ai_api.LLM import chat
from typing import List,Literal,Dict
from .Summarizer import BasicThreadSummarizer

class MainChatBot:
  def __init__(self,template:chat.ChatTemplate,model:Literal["gpt3.5","gpt4o","glm3","glm4","glm4v"]|None=None):
    self.mainEntity = template.to_entity(BasicThreadSummarizer())
    self.model_setting=model if model else "glm3"
    self.img_url_cache=[]
    
  def single_chat(self,text:str, model:Literal["gpt3.5","gpt4o","glm3","glm4","glm4v"]|None=None):
    if model:
      self.model_setting=model
    
    return self.mainEntity(text,self.model_setting,self.img_url_cache)

  def add_img_to_next_chat(self,img_url:str):
    self.img_url_cache.append(img_url)
    
  def save_chat(self,path):
    self.mainEntity.thread.save_thread(path)