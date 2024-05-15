from openai.types.create_embedding_response import CreateEmbeddingResponse
from openai.types.chat.chat_completion import ChatCompletion
import zhipuai
import openai
from ... import initialization_tool
from typing import List,Literal,Dict
keys=initialization_tool.config


model_name={"gpt3.5":"gpt-3.5-turbo","gpt4o":"gpt-4o","glm3":"glm-3-turbo","glm4":"glm-4","glm4v":"glm-4v","e3l":"text-embedding-3-large","e3s":"text-embedding-3-small","ze2":"embedding-2"}

oa_model=["gpt-3.5-turbo","gpt-4o","text-embedding-3-large","text-embedding-3-small"]
zp_model=["glm-3-turbo","glm-4","glm-4v","embedding-2"]

class MainClient():
    def __init__(self):
        self.oa=openai.Client(api_key=keys["openai_key"],base_url="https://openkey.cloud/v1")
        self.zp=openai.Client(api_key=keys["zhipu_key"],base_url="https://open.bigmodel.cn/api/paas/v4/")
    
    
    def chat(self,**kwargs)->ChatCompletion:
      model=model_name.get(kwargs["model"])
      if not model:
        model=kwargs["model"]
        if not model in model_name.values():
          raise ValueError("model not found")
        
      if model in oa_model:
        return self.oa.chat.completions.create(**kwargs)
      elif model in zp_model:
        return self.zp.chat.completions.create(**kwargs)
      
    def embedding(self,**kwargs)->CreateEmbeddingResponse:
      model=model_name.get(kwargs["model"])
      if not model:
        if not model in model_name.values():
          raise ValueError("model not found")
        
      if model in oa_model:
        return self.oa.embeddings.create(**kwargs)
      elif model in zp_model:
        return self.zp.embeddings.create(**kwargs)
        


main_client=MainClient()