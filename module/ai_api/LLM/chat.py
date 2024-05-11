from dataclasses import dataclass
import json
import zhipuai
import openai
from ..Client.client import main_client
from ... import initialization_tool
from typing import List,Literal,Dict
keys=initialization_tool.config

client_oa=openai.Client(api_key=keys["openai_key"],base_url="https://openkey.cloud/v1")
client_zp=openai.Client(api_key=keys["zhipu_key"],base_url="https://open.bigmodel.cn/api/paas/v4/")
#客户端要统一


model_name={"gpt3.5":"gpt-3.5-turbo","gpt4":"gpt-4-turbo","glm3":"glm-3-turbo","glm4":"glm-4","glm4v":"glm-4v","e3l":"text-embedding-3-large","e3s":"text-embedding-3-small","ze2":"embedding-2"}

@dataclass
class ThreadMetaData:
  time:int
  title:str
  summary:str
  key_words:List[str]
  embedding:List[float]
  
  def to_dict(self):
    return {
      "time":self.time,
      "title":self.title,
      "summary":self.summary,
      "key_words":self.key_words,
      "embedding":self.embedding
    }
  
class ThreadSummarizerBase:
    def summarize(self, full_msg:str)->ThreadMetaData:
      raise NotImplementedError
    
class ChatTemplate:
  def __init__(self, system_prompt, temp=0.8, top_p=0.7, max_tokens=1024, additional_tools:List=[], json_response=False):
    self.system_prompt = system_prompt
    self.temp = temp
    self.top_p = top_p
    self.max_tokens = max_tokens
    self.additional_tools=additional_tools
    self.response_format={"type": "json_object"} if json_response else None
    self._tools=[]
  
  def __call__(self, message:str, model:Literal["gpt3.5","gpt4","glm3","glm4","glm4v"]="glm3"):
    messages=[{"role":"system","content":self.system_prompt},{"role":"user","content":message}]   
    tools=[tool.to_dict() for tool in self.additional_tools+self._tools]
    completion=main_client.chat(
      messages=messages,
      model=model_name[model],
      response_format=self.response_format,
      temperature=self.temp,
      top_p=self.top_p,
      max_tokens=self.max_tokens,
      tools=tools if len(tools)>0 else None
    )
    return completion
  
  def to_entity(self,summarizer:ThreadSummarizerBase=None):
    return ChatEntity(self,ChatThread(summarizer))

    
  
class ChatThread:
  def __init__(self,summarizer:ThreadSummarizerBase=None) -> None:
    self.messages=[]
    self.meta_data=None
    self.summarizer=summarizer if summarizer else ThreadSummarizerBase()
    
    
  def add_message(self, message:str|List[Dict], role:Literal["system","user"]="user"):
    self.messages.append({"role":role,"content":message})
  
  def create_vision_message(self, message:str, img_url:List[str]):
    msg_list=[{"type":"text","text":message}]
    for img in img_url:
      msg_list.append({"type":"image","image":img})
    self.messages.append({"role":"user","content":msg_list})
  
  def full_chat_str(self) -> str:
    chat=""
    for msg in self.messages:
      if isinstance(msg["content"], list):
        chat+=msg["role"]+":"+msg[0]["text"]+"\n"
      else:
        chat+=msg["role"]+":"+msg["content"]+"\n"
    return chat
  
    
  def save_thread(self, file_path:str):
    self.meta_data=self.summarizer.summarize(self.full_chat_str())
    with open(file_path,"w") as f:
      f.write(json.dumps({"messages":self.messages,"meta_data":self.meta_data.to_dict()}))
  
  def load_thread(self, file_path:str):
    with open(file_path,"r") as f:
      data=json.loads(f.read())
      self.messages=data["messages"]
      self.meta_data=ThreadMetaData(**data["meta_data"])
    
    
class ChatEntity:
  def __init__(self, template:ChatTemplate, thread:ChatThread) -> None:
    self.template=template
    self.thread=thread
  
  def __call__(self, message:str, model:Literal["gpt3.5","gpt4","glm3","glm4","glm4v"]="glm3", img_url:List[str]=[]):
    if img_url:
      self.thread.create_vision_message(message, img_url)
    else:
      self.thread.add_message(message)
    messages=[{"role":"system","content":self.template.system_prompt}]+self.thread.messages
    tools=[tool.to_dict() for tool in self.template.additional_tools+self.template._tools]
    completion=main_client.chat(
      messages=messages,
      model=model_name[model],
      response_format=self.template.response_format,
      temperature=self.template.temp,
      top_p=self.template.top_p,
      max_tokens=self.template.max_tokens,
      tools=tools if len(tools)>0 else None
    )
    return completion
  
  def change_thread(self,thread:ChatThread):
    o_thread=self.thread
    self.thread=thread
    return o_thread
  
    