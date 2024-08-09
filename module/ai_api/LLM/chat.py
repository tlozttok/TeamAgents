from dataclasses import dataclass
import json
import zhipuai
import openai
from ..Client.client import main_client
from ... import initialization_tool
from typing import Any, Callable, List, Literal, Dict
from .models import ModelType
keys = initialization_tool.config

client_oa = openai.Client(
    api_key=keys["openai_key"], base_url="https://openkey.cloud/v1")
client_zp = openai.Client(
    api_key=keys["zhipu_key"], base_url="https://open.bigmodel.cn/api/paas/v4/")
# 客户端要统一


class ToolParameter:
    def __init__(self, name: str, description: str, type: str, required: bool = True) -> None:
        self.name = name
        self.description = description
        self.type = type


class Tool:
    name: str
    description: str
    parameters: List[ToolParameter]
    required: List[str]
    function: Callable[[Any,], dict]

    def __init__(self, name: str, description: str, function: Callable[[str], str]) -> None:
        self.name = name
        self.description = description
        self.parameters = []
        self.required = []
        self.function = function

    def to_dict(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        param.name: {
                            "type": param.type,
                            "description": param.description
                        }
                        for param in self.parameters
                    },
                    "required": self.required
                }
            }
        }

    def call(self,para:str):
        para_dict=json.loads(para)
        result=self.function(**para_dict)
        return json.dumps(result)



@dataclass
class ThreadMetaData:
    time: int
    title: str
    summary: str
    key_words: List[str]
    embedding: List[float]

    def to_dict(self):
        return {
            "time": self.time,
            "title": self.title,
            "summary": self.summary,
            "key_words": self.key_words,
            "embedding": self.embedding
        }


class ThreadSummarizerBase:
    def summarize(self, full_msg: str) -> ThreadMetaData:
        raise NotImplementedError


class ThreadMetadataComparerBase:
    def compare(self, thread1: ThreadMetaData, thread2: ThreadMetaData):
        raise NotImplementedError


class ChatTemplate:
    def __init__(self, system_prompt, temp=0.8, top_p=0.7, max_tokens=1024, additional_tools: List = [], json_response=False):
        self.system_prompt = system_prompt
        self.temp = temp
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.additional_tools = additional_tools
        self.response_format = {
            "type": "json_object"} if json_response else None
        self._tools = []

    def call_functions(self, completion):
        calls=completion.choices[0].message.tool_calls
        result_message=[]
        for call in calls:
            args=call.function.arguments
            name=call.function.name
            for function in self._tools+self.additional_tools:
                if function.name==name:
                    result=function.call(args)
                    result_message.append({"role": "tool", "tool_call_id": completion.choices[0].message.tool_calls[0].id,
                             "content": result})
        return result_message

    def __call__(self, message: str, model: ModelType = ModelType.GLM4):
        done=False
        messages = [{"role": "system", "content": self.system_prompt}, {
            "role": "user", "content": message}]
        tools = [tool.to_dict() for tool in self.additional_tools+self._tools]
        while not done:
            completion = main_client.chat(
                messages=messages,
                model=model,
                response_format=self.response_format,
                temperature=self.temp,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                tools=tools if len(tools) > 0 else None
            )
            if completion.choices[0].finish_reason=="tool_calls":
                messages+=self.call_functions(completion)
            else:
                done=True
        return completion

    def to_entity(self, summarizer: ThreadSummarizerBase = None):
        return ChatEntity(self, ChatThread(summarizer))


class ChatThread:
    def __init__(self, summarizer: ThreadSummarizerBase = None) -> None:
        self.messages = []
        self.meta_data = None
        self.summarizer = summarizer if summarizer else ThreadSummarizerBase()

    def add_message(self, message: str | List[Dict], role: Literal["assistant", "user"] = "user"):
        self.messages.append({"role": role, "content": message})

    def create_vision_message(self, message: str, img_url: List[str]):
        msg_list = []
        for img in img_url:
            msg_list.append({"type": "image_url", "image_url": {
                            "url": img}})
        msg_list.append({"type": "text", "text": message})
        self.messages.append({"role": "user", "content": msg_list})

    def full_chat_str(self) -> str:
        chat = ""
        for msg in self.messages:
            if isinstance(msg["content"], list):
                chat += msg["role"]+":"+msg[0]["text"]+"\n"
            else:
                chat += msg["role"]+":"+msg["content"]+"\n"
        return chat

    def save_thread(self, file_path: str):
        self.meta_data = self.summarizer.summarize(self.full_chat_str())
        with open(file_path, "a") as f:
            f.write("\n")
            f.write(json.dumps({"messages": self.messages,
                    "meta_data": self.meta_data.to_dict()}))

    def thread_save_data(self) -> str:
        self.meta_data = self.summarizer.summarize(self.full_chat_str())
        return json.dumps({"messages": self.messages,
                           "meta_data": self.meta_data.to_dict()})

    def load_thread_data(self, data: str):
        t_data = json.loads(data)
        self.messages = t_data["messages"]
        self.meta_data = ThreadMetaData(**t_data["meta_data"])

    @property
    def first_user_message(self) -> str:
        content = self.messages[0]["content"]
        if isinstance(content, list):
            return content[-1]["text"]
        else:
            return self.messages[0]["content"]


class ChatEntity:
    def __init__(self, template: ChatTemplate, thread: ChatThread) -> None:
        self.template = template
        self.thread = thread

    def __call__(self, message: str, model: ModelType = ModelType.GLM4, img_url: List[str] = []):
        if img_url:
            self.thread.create_vision_message(message, img_url)
        else:
            self.thread.add_message(message)
        messages = [
            {"role": "system", "content": self.template.system_prompt}]+self.thread.messages
        tools = [tool.to_dict()
                 for tool in self.template.additional_tools+self.template._tools]
        completion = main_client.chat(
            messages=messages,
            model=model,
            response_format=self.template.response_format,
            temperature=self.template.temp,
            top_p=self.template.top_p,
            max_tokens=self.template.max_tokens,
            tools=tools if len(tools) > 0 else None
        )
        self.thread.add_message(
            completion.choices[0].message.content, "assistant")
        return completion
