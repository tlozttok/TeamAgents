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
  user_obj:GuildUser
  current_channel:Channel
  guild:int
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
    
  
  def _register_user(self,user_id:int,user_name:str,user_obj:GuildUser,current_channel,guild,model:Literal["gpt3.5","gpt4o","glm3","glm4","glm4v"]="glm3"):
    self.users_information[user_id]=user_information(user_id,user_name,user_obj,current_channel,guild,model)  
  
  async def _reg_user_with_msg(self,msg:Message,model:Literal["gpt3.5","gpt4o","glm3","glm4","glm4v"]="glm3"):
    channel=await self.bot.fetch_public_channel(msg.target_id)
    self._register_user(msg.author_id,msg.author.username,msg.author,channel,msg.extra["guild_id"],model
    )

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
  
  def _single_chat_reg(self):  
    @self.bot.command(name="单人对话",aliases=["drdh","dh","对话"])
    async def single_chat(msg:Message,*args):
      user_id=msg.author_id
      
      if not self.users_information.get(msg.author_id):
        await self._reg_user_with_msg(msg,"glm4")
      else:
        self.users_information[msg.author_id].current_channel=msg.target_id
        
      if len(args)>=1 and (args[0] not in initialization_tool.model_list):
        await msg.reply("没有这个模型哦~")
        return
      elif len(args)>=1:
        self.users_information[user_id].model=args[0]
      chatbot=mc.MainChatBot(self.template,self.users_information[user_id].model)
      self.user_bot[user_id]=chatbot
      if len(args)>=3:
        self.user_state[user_id]=asyncio.create_task(self._end_user_single_chat(user_id,(int(args[1]),int(args[2])))),int(args[1]),int(args[2])
      else:
        self.user_state[user_id]=asyncio.create_task(self._end_user_single_chat(user_id)),60,60
      await msg.reply("对话创建成功❤️")
  
  def _single_chat_reply_reg(self):
    #记得注册处理其他消息，还要判断用户是否正在单人对话
    @self.bot.on_message()
    async def single_chat_reply(msg:Message):
      user_id=msg.author_id
      if self.user_bot.get(user_id) is not None:
        self.user_state[user_id][0].cancel()
        chatbot=self.user_bot[user_id]
        response=chatbot.single_chat(msg.content)
        self.users_information[user_id].user_usage+=usage(response.usage.prompt_tokens,response.usage.completion_tokens,response.usage.total_tokens)
        await msg.reply(response.choices[0].message.content)
        w1,w2=self.user_state[user_id][1],self.user_state[user_id][2]
        self.user_state[user_id]=asyncio.create_task(self._end_user_single_chat(user_id,(w1,w2))),w1,w2
  
  async def _end_user_single_chat(self,user_id:int,wait_time:Tuple[int]=(60,60)):
    if self.users_information.get(user_id) is not None:
      await asyncio.sleep(wait_time[0])
      await self.users_information[user_id].current_channel.send(f"{self.users_information[user_id].name}，不说话的话，再过{wait_time[0]}秒本次对话就要结束啦")
      await asyncio.sleep(wait_time[1])
      await self.users_information[user_id].current_channel.send(f"@{self.users_information[user_id].name} ，对话已经结束🐙")
      self.user_bot.pop(user_id).save_chat(keys['chat_save'])
      self.user_state.pop(user_id)
  
  def run(self):
    self._chat_once_reg()
    self._single_chat_reg()
    self._single_chat_reply_reg()
    self.bot.run()