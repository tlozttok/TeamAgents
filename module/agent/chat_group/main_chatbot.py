from ...ai_api.LLM import chat, models
from typing import List, Literal, Dict
from .Summarizer import BasicThreadSummarizer
from ...initialization_tool import config


class CommonChatBot:

    mainEntity: chat.ChatEntity
    model_setting: models.ModelType
    img_url_cache: List[str]
    threads: List[chat.ChatThread]
    thread_save_path: str
    activate_thread: chat.ChatThread
    input_token: int
    reply_token: int

    def __init__(self, template: chat.ChatTemplate, model: models.ModelType = models.ModelType.GLM4):
        self.mainEntity = template.to_entity(BasicThreadSummarizer())
        self.model_setting = model
        self.img_url_cache = []
        self.threads = []
        self.thread_save_path = config["chat_save_path"]
        self.activate_thread = self.mainEntity.thread
        self.input_token = 0
        self.reply_token = 0

    def set_model(self, model: models.ModelType):
        self.model_setting = model

    def create_new_chat(self, thread: chat.ChatThread = None) -> None:
        if thread:
            new_thread = thread
        else:
            new_thread = chat.ChatThread(BasicThreadSummarizer())

        self.threads.append(new_thread)
        self.activate_thread = new_thread
        self.mainEntity.thread = new_thread

    def end_current_chat(self):
        self.activate_thread = None
        self.mainEntity.thread = None

    def save_chat(self, chat_id: int):
        thread = self.threads[chat_id]
        thread.save_thread(self.thread_save_path)
        self.threads.remove(thread)

    def save_all_chat(self):
        for thread in self.threads:
            thread.save_thread(self.thread_save_path)
            self.threads.remove(thread)

    def change_chat(self, chat_id: int):
        self.activate_thread = self.threads[chat_id]

    def get_chat_list(self) -> List[str]:
        # 用第一个用户消息做标识符吧，可以搞一个卡片消息
        ...

    def send_message(self, message: str):
        reply = self.mainEntity(
            message, self.model_setting, self.img_url_cache)
        self.input_token += reply.usage.prompt_tokens
        self.reply_token += reply.usage.completion_tokens
        if reply.choices[0].message.content:
            return reply.choices[0].message.content
        elif reply.choices[0].message.tool_calls:
            ...

    def add_img_to_next_chat(self, img_url: str):
        self.img_url_cache.append(img_url)

    def save_chat(self, path):
        self.mainEntity.thread.save_thread(path)
