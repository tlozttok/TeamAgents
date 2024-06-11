import asyncio
from khl import Bot, Message, Event, EventTypes, MessageTypes, GuildUser, Channel
from .. import initialization_tool
from ..ai_api.LLM import chat
from ..agent.chat_group import main_chatbot as mc
from dataclasses import dataclass, field
from typing import List, Literal, Dict, Tuple

keys = initialization_tool.config


class MsgLayer:
    bot: Bot
    user_state: Dict[int, Tuple[asyncio.Task, int, int]]

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.user_state = {}

    def _reg_chat_once_msg(self):
        @self.bot.command(regex=r"(?i)^((?:饭田|Marina)[,，].+)")
        async def chat_once_group(msg: Message, content: str):
            await msg.reply("[程序测试]"+content)

        @self.bot.on_message()
        async def chat_once_person(msg: Message):
            print("111")
            user = msg.author
            await user.send("111")

    def _reg_create_single_chat(self):
        @self.bot.command(name="chat", aliases=["聊天", "c"])
        async def create_single_chat(msg: Message, content: str):
            ...

    def run(self):
        self._reg_chat_once_msg()
        self.bot.run()
