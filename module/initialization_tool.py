import json

def read_secret(path):
  #读取json文件
  with open(path, 'r', encoding='utf-8') as f:
    return json.load(f)
  
config=read_secret("./secret.json")
model_list=["gpt3.5","gpt4","glm3","glm4","glm4v"]