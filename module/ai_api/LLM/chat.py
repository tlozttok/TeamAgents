import zhipuai
import openai
from ... import initialization_tool
from typing import List,Literal,Dict
keys=initialization_tool.keys

client_oa=openai.Client(api_key=keys["openai_key"],base_url="https://openkey.cloud/v1")
client_zp=openai.Client(api_key=keys["zhipu_key"],base_url="https://open.bigmodel.cn/api/paas/v4/")
#客户端要统一

model_name={"gpt3.5":"gpt-3.5-turbo","gpt4":"gpt-4-turbo","glm3":"glm-3-turbo","glm4":"glm-4","glm4v":"glm-4v"}

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
    completion=client_zp.chat.completions.create(
      messages=messages,
      model=model_name[model],
      response_format=self.response_format,
      temperature=self.temp,
      top_p=self.top_p,
      max_tokens=self.max_tokens,
      tools=tools if len(tools)>0 else None
    )
    return completion
  
  def to_entity(self):
    return ChatEntity(self,ChatThread())
  
class ChatThread:
  def __init__(self) -> None:
    self.messages=[]
    
  def add_message(self, message:str|List[Dict], role:Literal["system","user"]="user"):
    self.messages.append({"role":role,"content":message})
  
  def create_vision_message(self, message:str, img_url:List[str]):
    msg_list=[{"type":"text","text":message}]
    for img in img_url:
      msg_list.append({"type":"image","image":img})
    self.messages.append({"role":"user","content":msg_list})
    
    
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
    completion=client_zp.chat.completions.create(
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
  
    