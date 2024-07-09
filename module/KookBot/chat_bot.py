import asyncio
from khl import Bot, Message, Event, EventTypes, MessageTypes, GuildUser, Channel
from .. import initialization_tool
from ..ai_api.LLM import chat
from ..agent.chat_group import main_chatbot as mc
from dataclasses import dataclass, field
from typing import List, Literal, Dict, Tuple
from ..ai_api.LLM.models import ModelType

keys = initialization_tool.config


@dataclass
class usage():
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __iadd__(self, other):
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens
        return self

    def __add__(self, other):
        return usage(self.prompt_tokens+other.prompt_tokens, self.completion_tokens+other.completion_tokens, self.total_tokens+other.total_tokens)


@dataclass
class user_information():
    id: int
    name: str
    model: Literal["gpt3.5", "gpt4o", "glm3", "glm4", "glm4v"] = "glm3"
    user_usage: usage = field(default_factory=usage)


class BotMarina():
    chatbot: mc.CommonChatBot
    template: chat.ChatTemplate
    user_bot: Dict[int, mc.CommonChatBot]

    def __init__(self, chat_template: chat.ChatTemplate):
        self.template = chat_template
        self.user_bot = {}

    def register_user(self, user_id: int):
        self.user_bot[user_id] = mc.CommonChatBot(self.template)

    def chat_once(self, content: str, model: ModelType = ModelType.GLM4) -> str:
        return self.template(content, model).choices[0].message.content

    def new_single_chat(self, user_id: int):
        if user_id not in self.user_bot:
            self.register_user(user_id)

        self.user_bot[user_id].create_new_chat()

    def change_model(self, user_id: int, model: str):
        if model:
            self.user_bot[user_id].set_model(ModelType(model))
        else:
            self.user_bot[user_id].set_model(ModelType.GLM4)

    def send_message(self, user_id: int, message: str):
        return self.user_bot[user_id].send_message(message)

    def add_image_message(self, user_id: int, img_url: str):
        self.user_bot[user_id].add_img_to_next_chat(img_url)

    def end_single_chat(self, user_id: int):
        self.user_bot[user_id].end_current_chat()

    def change_chat(self, user_id: int, chat_id: int):
        self.user_bot[user_id].change_chat(chat_id)

    def get_chat_list(self, user_id: int):
        return self.user_bot[user_id].get_chat_list()

    def _chat_once_reg(self):
        @ self.bot.command(regex=r"(?i)^((?:饭田|Marina)[,，].+)")
        async def chat_once(msg: Message, content: str):
            if not self.users_information.get(msg.author_id):
                await self._reg_user_with_msg(msg, "glm4")
            else:
                self.users_information[msg.author_id].current_channel = msg.target_id
            response = self.template(
                content, self.users_information[msg.author_id].model)
            self.users_information[msg.author_id].user_usage += usage(
                response.usage.prompt_tokens, response.usage.completion_tokens, response.usage.total_tokens)
            await msg.reply(response.choices[0].message.content)
