from ...ai_api.LLM import chat, models
from typing import List, Literal, Dict
from .Summarizer import BasicThreadSummarizer
from ...initialization_tool import config
from ...initialization_tool import today


class CommonChatBot:

    mainEntity: chat.ChatEntity
    model_setting: models.ModelType
    img_url_cache: List[str]
    threads: List[chat.ChatThread]
    thread_save_path: str
    activate_thread: chat.ChatThread
    input_token: int
    reply_token: int

    def __init__(self, template: chat.ChatTemplate, thread_save_path: str = None, model: models.ModelType = models.ModelType.GLM4AIR):
        self.mainEntity = template.to_entity(BasicThreadSummarizer())
        self.model_setting = model
        self.img_url_cache = []
        self.threads = []
        self.thread_save_path = thread_save_path+"/"+today + \
            ".txt" if thread_save_path else config["chat_save_path"] + \
            "/"+today+".json"
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
        if self.activate_thread and len(self.activate_thread.messages) == 0:
            self.threads.remove(self.activate_thread)
        self.activate_thread = None
        self.mainEntity.thread = None

    def save_chat(self, chat_id: int, fileIO=None):
        thread = self.threads[chat_id]
        chat_data = thread.thread_save_data()
        if fileIO:
            fileIO.write(chat_data)
        else:
            with open(self.thread_save_path, "a") as f:
                f.write(chat_data)
                f.write("\n")
        self.threads.remove(thread)

    def save_all_chat(self):
        self.end_current_chat()
        with open(self.thread_save_path, "a") as f:
            for thread in self.threads:
                chat_data = thread.thread_save_data()
                f.write(chat_data)

    def load_data_from_file(self, fileIO=None):
        if fileIO:
            chat_data = fileIO.read()
        else:
            with open(self.thread_save_path, "r") as f:
                chat_data = f.read()

    def change_chat(self, chat_id: int):
        self.activate_thread = self.threads[chat_id]
        self.mainEntity.thread = self.activate_thread

    def get_chat_list(self) -> List[str]:
        chat_list = []
        for thread in self.threads:
            chat_list.append(thread.first_user_message)
        return chat_list

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
