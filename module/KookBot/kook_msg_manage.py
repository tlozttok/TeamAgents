import asyncio
from khl import Bot, Message, Event, EventTypes, MessageTypes, GuildUser, Channel, ChannelPrivacyTypes
from .. import initialization_tool
from ..initialization_tool import logger
from ..ai_api.LLM import chat
from ..agent.chat_group import main_chatbot as mc
from dataclasses import dataclass, field
from typing import List, Literal, Dict, Tuple
from .chat_bot import BotMarina

keys = initialization_tool.config


class MsgLayer:
    bot: Bot
    user_state: Dict[int, Tuple[GuildUser, asyncio.Task, int]]
    backend: BotMarina

    def __init__(self, bot: Bot, template: chat.ChatTemplate) -> None:
        self.bot = bot
        self.user_state = {}
        self.backend = BotMarina(template)

    def chat_once(self, content: str, author: int) -> str:
        return self.backend.chat_once(content)

    def _reg_chat_once_msg(self):
        """
        注册一次性的聊天回复命令和消息监听器。

        该方法通过装饰器注册了一个命令处理程序和一个消息监听器，用于处理一次性聊天请求。
        在群组中，用户可以使用特定格式的命令触发一次性聊天回复；
        在私聊中，如果用户之前没有与机器人交互过，他们的第一条消息也将触发一次性聊天回复。
        """
        logger.info("注册一次性聊天回复命令和私聊消息监听器")

        @self.bot.command(regex=r"(?i)^((?:饭田|Marina)[,，].+)")
        async def chat_once_group(msg: Message, content: str):
            if msg.channel_type == ChannelPrivacyTypes.GROUP:
                await msg.reply(self.chat_once(content, msg.author.id))

        @self.bot.on_message(MessageTypes.AUDIO, MessageTypes.CARD, MessageTypes.FILE, MessageTypes.IMG, MessageTypes.SYS, MessageTypes.VIDEO)
        async def chat_once_person(msg: Message):
            if (msg.author.id not in self.user_state) and msg.channel_type == ChannelPrivacyTypes.PERSON:
                await msg.reply(self.chat_once(msg.content, msg.author.id))

    def _start_single_chat(self, author: GuildUser, msg_to_reply: Message, para: Dict[str, str]):
        """
        初始化单人聊天任务。

        此函数用于开始一个针对特定用户的单人聊天任务。它根据传入的参数配置任务，
        包括选择对话模型和设置延迟时间。一旦任务启动，它将用户的状态更新为正在聊天，
        不对话两次延迟时间后，对话会结束。

        :param author: 聊天任务的发起者，类型为GuildUser。
        :param msg_to_reply: 需要回复的消息对象，用于任务结束时的回复。
        :param para: 包含任务参数的字典，如模型选择和延迟时间设置。
        """
        logger.debug(f"初始化单人聊天任务,用户id:{author.id}")
        model = para.get("-m")
        delay_time = int(para.get("-d", 120))
        self.backend.new_single_chat(author.id)
        if model:
            self.backend.change_model(author, model)
        end_task = asyncio.create_task(
            self._end_single_chat_task(author, msg_to_reply, delay_time))

        self.user_state[author.id] = author, end_task, delay_time
        logger.debug(f"单人聊天任务初始化完成，用户id:{author.id}")

    def _end_single_chat(self, user_id: int):
        """
        结束与单个用户的聊天。
        将用户状态置为空，不取消任务，因为该函数可能在任务中被调用。
        """
        logger.debug(f"准备结束与单个用户的聊天，用户id:{user_id}")
        self.backend.end_single_chat(user_id)
        self.user_state.pop(user_id)
        logger.debug(f"结束了与单个用户的聊天，用户id:{user_id}")

    async def _end_single_chat_task(self, user: GuildUser, msg_to_reply: Message, delay: int):
        """
        异步函数，用于结束与单个用户的聊天。

        参数:
        - user: 参与聊天的用户对象。
        - msg_to_reply: 用于回复用户的消息对象。
        - delay: 结束聊天前的等待时间，以秒为单位。

        该函数首先等待指定的延迟时间，然后向用户发送即将结束对话的提示，
        再次等待相同的延迟时间后，正式结束对话，并从用户状态中移除该用户。
        """
        await asyncio.sleep(delay)
        await msg_to_reply.reply(f"如果不说话的话，再过{delay}秒对话就会结束哦")
        await asyncio.sleep(delay)
        await msg_to_reply.reply(f"{user.nickname}，对话结束")
        logger.info(f"正在结束用户id:{user.id}的聊天")
        self._end_single_chat(user.id)

    def _reg_create_single_chat(self):
        """
        注册一个命令，用于创建单人聊天会话。

        该命令通过bot命令系统注册，用户可以通过在聊天中发出特定命令来创建与机器人的单人聊天会话。
        命令格式化参数通过键值对的方式传递，每对参数之间用空格分隔，键值对以"-"开头。
        """
        logger.info("注册创建单人聊天会话的命令")

        @self.bot.command(name="chat", aliases=["聊天", "c"])
        async def create_single_chat(msg: Message, *para):
            logger.info(f"正在创建单人聊天会话，用户id:{msg.author.id}")
            if msg.author.id in self.user_state:
                self.user_state[msg.author.id][1].cancel()
                self._end_single_chat(msg.author.id)

            try:
                assert len(para) % 2 == 0
                para = dict(zip(para[::2], para[1::2]))
                assert all([p.startswith("-") for p in para.keys()])
                self._start_single_chat(msg.author, msg, para)
                await msg.reply("创建成功")
            except AssertionError as ae:
                logger.warning(f"id:{msg.author.id}的参数错误")
                print(e)
                await msg.reply("参数错误😡")
            except Exception as e:
                print(e)
                logger.warning(f"创建单人聊天会话失败，id:{msg.author.id}")
                await msg.reply("$^%*$%#%^&^%$^")

    def _reg_receive_single_chat_message(self):
        logger.info("注册单人聊天会话的监听器")

        @self.bot.on_message(MessageTypes.AUDIO, MessageTypes.CARD, MessageTypes.FILE, MessageTypes.IMG, MessageTypes.SYS, MessageTypes.VIDEO)
        async def receive_single_chat_text_message(msg: Message):
            if msg.author.id in self.user_state and not msg.content.startswith("/"):
                logger.trace(f"收到单人聊天会话的消息，用户id:{msg.author.id}")
                # 取消用来终止对话的任务
                self.user_state[msg.author.id][1].cancel()
                # 获取回复
                reply = self.backend.send_message(msg.author.id, msg.content)
                await msg.reply(reply)
                # 重新创建用来终止对话的任务
                self.user_state[msg.author.id] = self.user_state[msg.author.id][0], asyncio.create_task(
                    self._end_single_chat_task(msg.author, msg, self.user_state[msg.author.id][2])), self.user_state[msg.author.id][2]
                logger.trace(f"处理完成，用户id:{msg.author.id}")

        @self.bot.on_message(MessageTypes.TEXT, MessageTypes.KMD, MessageTypes.AUDIO, MessageTypes.CARD, MessageTypes.FILE, MessageTypes.SYS, MessageTypes.VIDEO)
        async def receive_single_chat_img_message(msg: Message):
            if msg.author.id in self.user_state and not msg.content.startswith("/"):
                logger.trace(f"收到单人聊天图片的消息，用户id:{msg.author.id}")
                self.user_state[msg.author.id][1].cancel()
                img_url = msg.content
                self.backend.add_image_message(msg.author.id, img_url)
                self.user_state[msg.author.id] = self.user_state[msg.author.id][0], asyncio.create_task(
                    self._end_single_chat_task(msg.author, msg, self.user_state[msg.author.id][2])), self.user_state[msg.author.id][2]
                logger.trace(f"处理完成，用户id:{msg.author.id}")

    def _reg_end_single_chat(self):
        logger.info("注册结束单人聊天会话的命令")

        @self.bot.command(name="end", aliases=["结束", "e"])
        async def end_single_chat(msg: Message):
            if msg.author.id in self.user_state:
                logger.info(f"正在结束用户id:{msg.author.id}的聊天")
                self.user_state[msg.author.id][1].cancel()
                self._end_single_chat(msg.author.id)
                await msg.reply("对话结束")
                logger.info(f"结束用户id:{msg.author.id}的聊天")

    def _reg_get_chat_list(self):
        logger.info("注册获取对话列表和更换对话的命令")

        def build_chat_list_message(chat_list: List[int]):
            chat_list_message = ""
            for id, chat in enumerate(chat_list):
                chat_list_message += f"**对话{id}：**\n“{chat}...”\n"
            return chat_list_message

        @self.bot.command(name="list", aliases=["对话列表", "l"])
        async def get_chat_list(msg: Message):
            logger.info(f"发送用户id:{msg.author.id}的对话列表")
            chat_list = self.backend.get_chat_list(msg.author.id)
            await msg.reply(build_chat_list_message(chat_list))

        @self.bot.command(name="change", aliases=["切换", "ch"])
        async def change_chat(msg: Message, *para):
            logger.info(f"切换用户id:{msg.author.id}的对话")
            if msg.author.id in self.user_state:
                self.user_state[msg.author.id][1].cancel()
                self._end_single_chat(msg.author.id)
            chat_id = int(para[0])
            para = para[1:]
            try:
                assert len(para) % 2 == 0
                para = dict(zip(para[::2], para[1::2]))
                assert all([p.startswith("-") for p in para.keys()])
                self._start_single_chat(msg.author, msg, para)
                self.backend.end_single_chat(msg.author.id)
                self.backend.change_chat(msg.author.id, chat_id)
                await msg.reply("切换成功")
                logger.info(f"切换用户id:{msg.author.id}的对话完毕")
            except Exception as e:
                print(e)
                await msg.reply("参数错误😡")

    def _reg_shut_down(self):
        @self.bot.on_shutdown
        async def shut_down(bot: Bot):
            logger.info("保存聊天记录")
            self.backend.save_all()
            logger.info("机器人关闭")
            await bot.client.offline()

        @self.bot.command(name="shutdown", aliases=["关闭"])
        async def shut_down_hard(msg: Message):
            await shut_down(self.bot)
            initialization_tool.shutdown(120)

    async def offline(self):
        logger.info("保存聊天记录")
        self.backend.save_all()
        logger.info("机器人关闭")
        await self.bot.client.offline()

    def _register_all(self):
        self._reg_chat_once_msg()
        self._reg_create_single_chat()
        self._reg_receive_single_chat_message()
        self._reg_end_single_chat()
        self._reg_get_chat_list()
        self._reg_shut_down()

    async def start(self):
        self._register_all()
        await self.bot.start()

    @property
    def is_free(self):
        return self.user_state == {}

    def run(self):
        self._register_all()
        self.bot.run()
