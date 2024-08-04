from module.ai_api.LLM.chat import ThreadMetaData
from module.ai_api.LLM.models import ModelType
from ...ai_api.Embedding.embedding import Embedding
from ...ai_api.LLM.chat import ThreadSummarizerBase, ChatTemplate, ThreadMetadataComparerBase
import time
import re
import json
from ...initialization_tool import logger


class BasicThreadSummarizer(ThreadSummarizerBase):
    def __init__(self, chat_model=ModelType.GLM4AIR, embedding_model=ModelType.ZP_EMBEDDING):
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.titleTemplate = ChatTemplate(
            "根据对话内容，总结一个标题。标题应该简明扼要，能够概括对话的主要内容。用json格式返回标题。例：{\"title\": \"标题\"}", json_response=True)
        self.summarizer = ChatTemplate(
            "根据对话内容，总结一个摘要。摘要应该能够概括对话的主要内容。用json格式返回摘要。例：{\"summary\": \"摘要\"}", json_response=True)
        self.keywordTemplate = ChatTemplate(
            "根据对话内容，总结一些关键词。关键词应该与对话的内容密切相关，这段对话的不同主题部分都应该有关键词。用json格式返回关键词列表。例：{\"keywords\": [\"关键词1\",\"关键词2\",\"关键词3\"]}", json_response=True)

    def summarize(self, full_msg: str) -> ThreadMetaData:
        success = [False, False, False]
        json_re = re.compile(r"\{[\s\S]*\}")
        while not success[0]:
            try:
                raw_title = self.titleTemplate(
                    full_msg, self.chat_model).choices[0].message.content
                title = json.loads(json_re.findall(raw_title)[0])["title"]
            except Exception as e:
                logger.warning("标题生成失败")
                logger.trace(f"title文本: {raw_title}")
            else:
                success[0] = True

        while not success[1]:
            try:
                raw_summary = self.summarizer(
                    full_msg, self.chat_model).choices[0].message.content
                summary = json.loads(json_re.findall(raw_summary)[0])[
                    "summary"]
            except Exception as e:
                logger.warning("摘要生成失败")
                logger.trace(f"summary文本: {raw_summary}")
            else:
                success[1] = True

        while not success[2]:
            try:
                raw_keywords = self.keywordTemplate(
                    full_msg, self.chat_model).choices[0].message.content
                keywords = json.loads(json_re.findall(raw_keywords)[0])[
                    "keywords"]
            except Exception as e:
                logger.warning("关键词生成失败")
                logger.trace(f"keywords文本: {raw_keywords}")
            else:
                success[2] = True

        timestamp = int(time.time())
        embedding = Embedding().get_embedding(full_msg, self.embedding_model)
        metadata = ThreadMetaData(
            timestamp, title, summary, keywords, embedding)
        return metadata


class ThreadMetadataComparer(ThreadMetadataComparerBase):
    # 再说
    ...
