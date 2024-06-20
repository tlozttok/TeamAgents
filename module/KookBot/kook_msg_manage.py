import asyncio
from khl import Bot, Message, Event, EventTypes, MessageTypes, GuildUser, Channel, ChannelPrivacyTypes
from .. import initialization_tool
from ..ai_api.LLM import chat
from ..agent.chat_group import main_chatbot as mc
from dataclasses import dataclass, field
from typing import List, Literal, Dict, Tuple
from .chat_bot import BotMarina

keys = initialization_tool.config


class MsgLayer:
    bot: Bot
    user_state: Dict[int, Tuple[GuildUser, asyncio.Task, int]]
    backend: BotMarina

    def __init__(self, bot: Bot, template: chat.ChatTemplate) -> None:
        self.bot = bot
        self.user_state = {}
        self.backend = BotMarina(template)

    def chat_once(self, content: str, author: int) -> str:
        return self.backend.chat_once(content)

    def _reg_chat_once_msg(self):
        @self.bot.command(regex=r"(?i)^((?:饭田|Marina)[,，].+)")
        async def chat_once_group(msg: Message, content: str):
            if msg.channel_type == ChannelPrivacyTypes.GROUP:
                await msg.reply(self.chat_once(content, msg.author.id))

        @self.bot.on_message()
        async def chat_once_person(msg: Message):
            if (msg.author.id not in self.user_state) and msg.channel_type == ChannelPrivacyTypes.PERSON:
                await msg.reply(self.chat_once(msg.content, msg.author.id))

    def _start_single_chat(self, author: GuildUser, msg_to_reply: Message, para: Dict[str, str]):
        model = para.get("-m")
        delay_time = int(para.get("-d", 120))
        self.backend.new_single_chat(author.id)
        if model:
            self.backend.change_model(author, model)
        end_task = asyncio.create_task(
            self._end_single_chat(author, msg_to_reply, delay_time))

        self.user_state[author.id] = author, end_task, delay_time

    async def _end_single_chat(self, user: GuildUser, msg_to_reply: Message, delay: int):
        await asyncio.sleep(delay)
        await msg_to_reply.reply(f"如果不说话的话，再过{delay}秒对话就会结束哦")
        await asyncio.sleep(delay)
        await msg_to_reply.reply(f"{user.nickname}，对话结束")
        self.backend.end_single_chat(user.id)
        self.user_state.pop(user.id)

    def _reg_create_single_chat(self):
        @self.bot.command(name="chat", aliases=["聊天", "c"])
        async def create_single_chat(msg: Message, *para):
            try:
                assert len(para) % 2 == 0
                para = dict(zip(para[::2], para[1::2]))
                assert all([p.startswith("-") for p in para.keys()])
                self._start_single_chat(msg.author, msg, para)
                await msg.reply("创建成功")
            except Exception as e:
                print(e)
                await msg.reply("参数错误😡")

    def _reg_receive_single_chat_message(self):
        @self.bot.on_message()
        # 以后可以加上检测是否是回复机器人的功能
        async def receive_single_chat_message(msg: Message):
            if msg.author.id in self.user_state and not msg.content.startswith("/"):
                # 取消用来终止对话的任务
                self.user_state[msg.author.id][1].cancel()
                # 获取回复
                reply = self.backend.send_message(msg.author.id, msg.content)
                await msg.reply(reply)
                # 重新创建用来终止对话的任务
                self.user_state[msg.author.id] = self.user_state[msg.author.id][0], asyncio.create_task(
                    self._end_single_chat(msg.author, msg, self.user_state[msg.author.id][2])), self.user_state[msg.author.id][2]

    def _reg_end_single_chat(self):
        @self.bot.command(name="end", aliases=["结束", "e"])
        async def end_single_chat(msg: Message):
            if msg.author.id in self.user_state:
                self.user_state[msg.author.id][1].cancel()
                self.backend.end_single_chat(msg.author.id)
                self.user_state.pop(msg.author.id)
                await msg.reply("对话结束")

    def run(self):
        self._reg_chat_once_msg()
        self._reg_create_single_chat()
        self._reg_receive_single_chat_message()
        self._reg_end_single_chat()
        self.bot.run()
