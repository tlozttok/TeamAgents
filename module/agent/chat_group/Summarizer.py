from module.ai_api.LLM.chat import ThreadMetaData
from ...ai_api.Embedding.embedding import Embedding
from ...ai_api.LLM.chat import ThreadSummarizerBase,ChatTemplate
import time
import re
import json

class BasicThreadSummarizer(ThreadSummarizerBase):
  def __init__(self,chat_model="glm3",embedding_model="ze2"):
    self.chat_model = chat_model
    self.embedding_model = embedding_model
    self.titleTemplate = ChatTemplate("根据对话内容，总结一个标题。标题应该简明扼要，能够概括对话的主要内容。用json格式返回标题。例：{\"title\": \"标题\"}",json_response=True)
    self.summarizer= ChatTemplate("根据对话内容，总结一个摘要。摘要应该能够概括对话的主要内容。用json格式返回摘要。例：{\"summary\": \"摘要\"}",json_response=True)
    self.keywordTemplate= ChatTemplate("根据对话内容，总结一些关键词。关键词应该与对话的内容密切相关，这段对话的不同主题部分都应该有关键词。用json格式返回关键词列表。例：{\"keywords\": [\"关键词1\",\"关键词2\",\"关键词3\"]}",json_response=True)
    
    
  def summarize(self, full_msg: str) -> ThreadMetaData:
    title = self.titleTemplate(full_msg,self.chat_model).choices[0].message.content
    summary = self.summarizer(full_msg,self.chat_model).choices[0].message.content
    keywords = self.keywordTemplate(full_msg,self.chat_model).choices[0].message.content
    json_re=re.compile(r"\{.*\}")
    title=json.loads(json_re.findall(title)[0])["title"]
    summary=json.loads(json_re.findall(summary)[0])["summary"]
    keywords=json.loads(json_re.findall(keywords)[0])["keywords"]
    timestamp=int(time.time())
    embedding=Embedding().get_embedding(full_msg,self.embedding_model)
    metadata=ThreadMetaData(timestamp,title,summary,keywords,embedding)
    return metadata
    
    