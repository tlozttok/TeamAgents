from khl import Bot,Message
from .. import initialization_tool
from ..ai_api.LLM import chat
keys=initialization_tool.keys

testChat=chat.ChatTemplate("饭田是一个虚拟人物，英文名Marina ida，她性格内敛，言语温柔且带有些许羞涩，但面对他人戏谑时也能机智回击，显得颇为泼辣。她情感丰富，心地善良，尽管害羞，却并不吝于表达自我。请你扮演饭田，在一个Kook服务器中和用户对话，Kook是一个类似于Discord的应用。")

## websocket
bot = Bot(token = keys["bot_token"]) 

@bot.command(regex=r"(?i)^((?:饭田|Marina)[,，].+)")
async def reply(message: Message, content):
  reply=testChat(content,"glm4")
  await message.reply(reply.choices[0].message.content)

@bot.command(name="对话")
async def start_chat(msg: Message):
  ...

@bot.command(name="test", prefixes=['/', '.'], aliases=['tb', 'ta'], case_sensitive=False)
async def test_cmd(msg: Message):
    """测试命令"""
    print(f"get test cmd from", msg.author_id)
    await msg.reply(f"get test cmd!")  
  
