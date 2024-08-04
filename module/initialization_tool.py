import json
import datetime
import sys
from loguru import logger
import subprocess

logger.remove()

logger.add(sink=sys.stdout, level="TRACE")

today = datetime.datetime.now().strftime("%Y-%m-%d")


def shutdown(time: int = 0):
    subprocess.run(["shutdown", "-s", "-t", str(time)])


def read_secret(path):
    # 读取json文件
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


config = read_secret("./secret.json")
model_list = ["gpt3.5", "gpt4o", "glm3", "glm4", "glm4v"]
