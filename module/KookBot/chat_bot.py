import asyncio
from khl import Bot,Message,Event,EventTypes,MessageTypes,GuildUser,Channel
from .. import initialization_tool
from ..ai_api.LLM import chat
from ..agent.chat_group import main_chatbot as mc
from dataclasses import dataclass, field
from typing import List,Literal,Dict, Tuple

keys=initialization_tool.config

@dataclass
class usage():
  prompt_tokens: int=0
  completion_tokens: int=0
  total_tokens:int=0
  
  def __iadd__(self,other):
    self.prompt_tokens+=other.prompt_tokens
    self.completion_tokens+=other.completion_tokens
    self.total_tokens+=other.total_tokens
    return self
  
  def __add__(self,other):
    return usage(self.prompt_tokens+other.prompt_tokens,self.completion_tokens+other.completion_tokens,self.total_tokens+other.total_tokens)
  
  
@dataclass
class user_information():
  id:int
  name:str
  model:Literal["gpt3.5","gpt4o","glm3","glm4","glm4v"]="glm3"
  user_usage:usage=field(default_factory=usage)

class KookChatBot():
  bot:Bot
  chatbot:mc.MainChatBot
  template:chat.ChatTemplate
  user_bot:Dict[int,mc.MainChatBot]
  users_information:Dict[int,user_information]
  user_state:Dict[int,Tuple[asyncio.Task,int,int]]
  def __init__(self,chat_template:chat.ChatTemplate):
    self.bot=Bot(token=keys['bot_token'])
    self.template=chat_template
    self.users_information={}
    self.user_bot={}
    self.user_state={}
    
  
  def _register_user(self,user_id:int,user_name:str,model:Literal["gpt3.5","gpt4o","glm3","glm4","glm4v"]="glm3"):
    self.users_information[user_id]=user_information(user_id,user_name,model)  

  def _chat_once_reg(self):  
    @self.bot.command(regex=r"(?i)^((?:饭田|Marina)[,，].+)")  
    async def chat_once(msg:Message,content:str):
      if not self.users_information.get(msg.author_id):
        await self._reg_user_with_msg(msg,"glm4")
      else:
        self.users_information[msg.author_id].current_channel=msg.target_id
      response=self.template(content,self.users_information[msg.author_id].model)
      self.users_information[msg.author_id].user_usage+=usage(response.usage.prompt_tokens,response.usage.completion_tokens,response.usage.total_tokens)
      await msg.reply(response.choices[0].message.content)
  
  