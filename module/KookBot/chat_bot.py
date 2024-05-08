from khl import Bot,Message,Event,EventTypes,MessageTypes
from .. import initialization_tool
from ..ai_api.LLM import chat
from ..agent.chat_group import main_chatbot as mc
from dataclasses import dataclass, field
from typing import List,Literal,Dict
keys=initialization_tool.keys

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
  user_id:int
  user_name:str
  model:Literal["gpt3.5","gpt4","glm3","glm4","glm4v"]="glm3"
  user_usage:usage=field(default_factory=usage)

class KookChatBot():
  bot:Bot
  chatbot:mc.MainChatBot
  template:chat.ChatTemplate
  user_bot:Dict[int,mc.MainChatBot]
  users_information:Dict[int,user_information]
  def __init__(self,chat_template:chat.ChatTemplate):
    self.bot=Bot(token=keys['bot_token'])
    self.template=chat_template
    self.users_information={}
    self.user_bot={}
  
  def _register_user(self,user_id:int,user_name:str,model:Literal["gpt3.5","gpt4","glm3","glm4","glm4v"]="glm3"):
    self.users_information[user_id]=user_information(user_id,user_name,model)  
    
  def _chat_once_reg(self):  
    @self.bot.command(regex=r"(?i)^((?:饭田|Marina)[,，].+)")  
    async def chat_once(msg:Message,content:str):
      if not self.users_information.get(msg.author_id):
        self._register_user(msg.author_id,msg.author.username,"glm4")
      response=self.template(content,self.users_information[msg.author_id].model)
      self.users_information[msg.author_id].user_usage+=usage(response.usage.prompt_tokens,response.usage.completion_tokens,response.usage.total_tokens)
      await msg.reply(response.choices[0].message.content)
  
  def _single_chat_reg(self):  
    @self.bot.command(name="单人对话",aliases=["drdh","dh","对话"])
    async def single_chat(msg:Message,*args):
      user_id=msg.author_id
      
      if not self.users_information.get(msg.author_id):
        self._register_user(msg.author_id,msg.author.username,"glm4")
        
      if len(args)>=1 and (args[0] not in initialization_tool.model_list):
        await msg.reply("没有这个模型哦~")
        return
      elif len(args)>=1:
        self.users_information[user_id].model=args[0]
      chatbot=mc.MainChatBot(self.template.to_entity(),self.users_information[user_id].model)
      self.user_bot[user_id]=chatbot
      await msg.reply("对话创建成功❤️")
  
  def _single_chat_reply_reg(self):
    #记得注册处理其他消息，还要判断用户是否正在单人对话
    @self.bot.on_message()
    async def single_chat_reply(msg:Message):
      user_id=msg.author_id
      if self.user_bot.get(user_id) is not None:
        chatbot=self.user_bot[user_id]
        response=chatbot.single_chat(msg.content)
        self.users_information[user_id].user_usage+=usage(response.usage.prompt_tokens,response.usage.completion_tokens,response.usage.total_tokens)
        await msg.reply(response.choices[0].message.content)
  
  async def _end_user_single_chat(self,user_id:int):
    ...
  
  def run(self):
    self._chat_once_reg()
    self._single_chat_reg()
    self._single_chat_reply_reg()
    self.bot.run()