from __future__ import annotations

import asyncio
import hashlib
import json
import queue
import random
import re
import uuid
from typing import Dict, List, Optional, Tuple, Union

import aiohttp
from aiohttp_socks import ProxyConnector
from loguru import logger

from .type import ChatCodeUpdate, ChatTiTleUpdate, SuggestRely, Text, TextCancel
from .util import (
    CONST_NAMESPACE,
    GQL_URL,
    HOME_URL,
    SETTING_URL,
    async_retry,
    generate_data,
    generate_nonce,
)


class Poe_Client:
    def __init__(self, p_b: str, formkey: str, proxy: Optional[str] = ""):
        self.channel_url: str = ""
        self.bots: dict = {}
        self.queues: Dict[str, queue.Queue] = {}
        self.wss = None
        self.wss_task: asyncio.Task = None
        self.bot_lock: Dict[str, asyncio.Lock] = {}
        self.bot_crt_msg_id: Dict[str, int] = {}
        self.chat_lock: Dict[str, asyncio.Lock] = {}
        self.formkey: str = formkey
        self.p_b: str = p_b
        self.sdid: str = ""
        self.subscription: dict = {}
        self.tchannel_data: dict = {}
        self.user_id: str = ""
        self.viewer: dict = {}
        self.ws_domain = f"tch{random.randint(1, int(1e6))}"[:8]
        self.proxy = proxy
        self.salt = "4LxgHM6KpFqokX0Ox"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": f"p-b={self.p_b}",
            "poe-formkey": self.formkey,
            "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="112"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Upgrade-Insecure-Requests": "1",
        }

    @property
    def bot_code_dict(self):
        return {
            bot: [chat for chat in data["chats"]] for bot, data in self.bots.items()
        }

    @property
    def session_args(self):
        args = {
            "headers": self.headers,
            "cookies": {"p-b": self.p_b},
        }
        if self.proxy:
            connector = ProxyConnector.from_url(self.proxy)
            args["connector"] = connector
        return args

    # 基本信息获取
    async def create(self, pre_load: bool = False):
        logger.info("Creating client -----")
        await self.get_basedata()

        if pre_load:
            await self.get_available_bots(get_all=True)
        logger.info("Succeed to create async_poe_client instance")
        return self

    @async_retry(3, "Failed to get base data")
    async def get_basedata(self) -> None:
        try:
            async with aiohttp.ClientSession(**self.session_args) as client:
                response = await client.get(HOME_URL, timeout=8)
                text = await response.text()
        except Exception as e:
            raise Exception("Failed to get basedata from home.") from e
        """extract next_data from html"""
        try:
            """get next_data"""
            json_regex = (
                r'<script id="__NEXT_DATA__" type="application\/json">(.+?)</script>'
            )
            json_text = re.search(json_regex, text).group(1)
            next_data = json.loads(json_text)
        except Exception as e:
            raise ValueError("Failed to extract 'next_data' from the response.") from e

        """extract data from next_data"""
        try:
            self.viewer = next_data["props"]["initialData"]["data"]["pageQuery"][
                "viewer"
            ]
            self.user_id = self.viewer["poeUser"]["id"]
            self.subscription = self.viewer["subscription"]
            bot_list = self.viewer["availableBotsConnection"]["edges"]
            for bot in bot_list:
                self.bots[bot["node"]["handle"]] = {}
            self.sdid = str(uuid.uuid5(CONST_NAMESPACE, self.viewer["poeUser"]["id"]))
        except KeyError as e:
            raise ValueError(
                "Failed to extract 'viewer' or 'user_id' from 'next_data'."
            ) from e

    @async_retry(3, "Failed to get channel data")
    async def get_channel_data(self) -> None:
        async with aiohttp.ClientSession(**self.session_args) as client:
            response = await client.get(SETTING_URL)
            data = await response.text()
            json_data = json.loads(data)
            self.tchannel_data = json_data["tchannelData"]
            self.headers["Poe-Tchannel"] = self.tchannel_data["channel"]
            self.channel_url = f'wss://{self.ws_domain}.tch.{self.tchannel_data["baseHost"]}/up/{self.tchannel_data["boxName"]}/updates?min_seq={self.tchannel_data["minSeq"]}&channel={self.tchannel_data["channel"]}&hash={self.tchannel_data["channelHash"]}'
            logger.info("succeed to get channel data")

    # chat 会话获取和操作
    # 获取会话列表
    @async_retry(3, "Failed to get chat list")
    async def get_chat_list(
        self, url_botname: str, count: int = 25, get_all: bool = False
    ):
        """获取某个bot的chat信息(包含chat_id, 只包含部分历史消息)"""
        get_count = 0

        if url_botname not in self.bots.keys():
            self.bots[url_botname] = {"bot": {}, "chats": {}}
        cursor = ""
        while get_count < count or get_all:
            data = await self.send_query(
                "ChatHistoryFilteredListPaginationQuery",
                {"count": 25, "cursor": cursor, "handle": url_botname},
            )
            cursor = data["data"]["filteredChats"]["pageInfo"]["endCursor"]
            edges = data["data"]["filteredChats"]["edges"]
            if not edges:
                logger.info(
                    f"Succeed to get all {get_count} messages with {url_botname}"
                )
                return self.bots[url_botname]["chats"]

            new_chats = {edge["node"]["chatCode"]: edge["node"] for edge in edges}
            get_count += len(new_chats)
            self.bots[url_botname]["chats"] = {
                **self.bots[url_botname]["chats"],
                **new_chats,
            }
        logger.info(f"Succeed to get {get_count} messages with {url_botname}")
        return self.bots[url_botname]["chats"]

    # 获取某个chat的信息
    @async_retry(3, "Failed to get chat")
    async def get_chat(self, url_botname: str, chat_code: str) -> dict:
        """主要用来获取某个chat的chat_id,也附带部分历史消息"""
        await self.ensure_botchat(url_botname, chat_code, load=False)

        data = await self.send_query("ChatPageQuery", {"chatCode": chat_code})

        self.bots[url_botname]["chats"][chat_code].update(data["data"]["chatOfCode"])
        return self.bots[url_botname][chat_code]

    # 获取某个chat的历史消息
    @async_retry(3, "Failed to get chat history")
    async def get_chat_history(
        self, url_botname: str, chat_code: str, count: int = 25, get_all: bool = False
    ):
        await self.ensure_botchat(url_botname, chat_code)
        if not (count or get_all):
            raise TypeError(
                "Please provide at least one of the following parameters: del_all=<bool>, count=<int>"
            )
        messages = self.bots[url_botname]["chats"][chat_code]["messagesConnection"][
            "edges"
        ]
        if len(messages) == 0:
            logger.error(
                f"Failed to get message history of {url_botname}: No messages found with {url_botname}"
            )
            return []
        cursor = messages[0]["cursor"]
        if not get_all and count <= len(messages):
            return messages[-count:]
        while get_all or (count > len(messages)):
            result = await self.send_query(
                "ChatListPaginationQuery",
                {
                    "count": 25,
                    "cursor": cursor,
                    "id": self.bots[url_botname]["chats"][chat_code]["id"],
                },
            )
            previous_messages = result["data"]["node"]["messagesConnection"]["edges"]
            messages = previous_messages + messages
            cursor = messages[0]["cursor"]
            if len(previous_messages) == 0:
                if not get_all:
                    logger.warning(
                        f"Only {str(len(messages))} history messages found with {url_botname}"
                    )
                break
        logger.info(f"Succeed to get messages from {url_botname}")
        if not get_all:
            return messages[-count:]
        else:
            return messages

    # 删除指定chatid的chat
    async def delete_chat_by_chat_id(self, chat_id: str):
        await self.send_query("useDeleteChat_deleteChat_Mutation", {"chatId": chat_id})
        logger.info(f"succeed to delete chat:{chat_id}")

    # 删除指定chatcode的chat
    async def delete_chat_by_chat_code(self, chat_code: str):
        result = {
            k: v for each in list(self.bots.values()) for k, v in each["chats"].items()
        }
        if chat_code not in result.keys():
            await self.get_available_bots(get_all=True)
        result = {
            k: v for each in list(self.bots.values()) for k, v in each["chats"].items()
        }
        await self.delete_chat_by_chat_id(result[chat_code]["chatId"])

    # 删除某个bot的指定数量的chat
    async def delete_chat_by_count(
        self, url_botname: str, count: int = 20, del_all: bool = False
    ):
        await self.ensure_botchat(url_botname)

        if not del_all:
            chats = list(self.bots[url_botname]["chats"].values())[:count]
            true_count = len(self.bots[url_botname]["chats"].keys())
            if count > true_count:
                logger.error(f"Only {true_count} chats with {url_botname} found.")
        else:
            chats = list(self.bots[url_botname]["chats"].values())
        tasks = []
        for chat in chats:
            tasks.append(
                asyncio.create_task(self.delete_chat_by_chat_id(chat["chatId"]))
            )
        await asyncio.gather(*tasks)

    # bot 获取和操作
    # 获取某个bot的信息
    @async_retry(3, "Failed to get bot")
    async def get_bot(self, url_botname: str) -> dict:
        """获取bot的信息,主要是为了获取bot的nickname,在发送消息时会用到"""
        data = await self.send_query("BotLandingPageQuery", {"botHandle": url_botname})
        await self.ensure_botchat(url_botname, load=False)
        self.bots[url_botname]["bot"].update(data["data"]["bot"])
        return self.bots[url_botname]["bot"]

    # 获取某个bot的设置信息
    @async_retry(3, "Failed to get bot setting")
    async def get_bot_setting(self, url_botname: str) -> dict:
        """获取bot的设置,比get_bot多了prompt等内容,在edit的时候用来保持未修改的值不变"""
        data = await self.send_query("editBotIndexPageQuery", {"botName": url_botname})
        if url_botname not in self.bots.keys():
            self.bots[url_botname] = {"bot": {}, "chats": {}}
        self.bots[url_botname]["bot"].update(data["data"]["bot"])
        return self.bots[url_botname]["bot"]

    # 获取所有可使用的bot
    @async_retry(3, "Failed to get available bots")
    async def get_available_bots(
        self, count: Optional[int] = 25, get_all: Optional[bool] = False
    ) -> dict:  # noqa: E501
        if not (get_all or count):
            raise TypeError(
                "Please provide at least one of the following parameters: get_all=<bool>, count=<int>"
            )
        response = await self.send_query(
            "availableBotsSelectorModalPaginationQuery", {}
        )  # noqa: E501
        bots = [
            each["node"]
            for each in response["data"]["viewer"]["availableBotsConnection"]["edges"]
            if each["node"]["deletionState"] == "not_deleted"
        ]
        cursor = response["data"]["viewer"]["availableBotsConnection"]["pageInfo"][
            "endCursor"
        ]
        if len(bots) >= count and not get_all:
            self.bots.update({bot["handle"]: {"bot": bot} for bot in bots})
            return self.bots
        while len(bots) < count or get_all:
            response = await self.send_query(
                "availableBotsSelectorModalPaginationQuery", {"cursor": cursor}
            )
            new_bots = [
                each["node"]
                for each in response["data"]["viewer"]["availableBotsConnection"][
                    "edges"
                ]
                if each["node"]["deletionState"] == "not_deleted"
            ]
            cursor = response["data"]["viewer"]["availableBotsConnection"]["pageInfo"][
                "endCursor"
            ]
            bots += new_bots
            if len(new_bots) == 0:
                if not get_all:
                    logger.error(f"Only {len(bots)} bots found on this account")
                else:
                    logger.info("Succeed to get all available bots")
                self.bots.update({bot["handle"]: {"bot": bot} for bot in bots})
                return self.bots
        logger.info("Succeed to get available bots")
        self.bots.update({bot["handle"]: {"bot": bot} for bot in bots})
        return self.bots

    # 获取bot市场中的bot
    @async_retry(3, "Failed to explore bots")
    async def explore_bots(
        self, count: int = 50, explore_all: bool = False
    ) -> List[dict]:
        bots = []
        result = await self.send_query(
            "ExploreBotsListPaginationQuery",
            {
                "count": count,
            },
        )
        new_cursor = result["data"]["exploreBotsConnection"]["edges"][-1]["cursor"]
        bots += [
            each["node"] for each in result["data"]["exploreBotsConnection"]["edges"]
        ]
        if len(bots) >= count and not explore_all:
            return bots[:count]
        while len(bots) < count or explore_all:
            result = await self.send_query(
                "ExploreBotsListPaginationQuery", {"count": count, "cursor": new_cursor}
            )
            if len(result["data"]["exploreBotsConnection"]["edges"]) == 0:
                if not explore_all:
                    logger.error(
                        f"No more bots could be explored,only {len(bots)} bots found."
                    )
                return bots
            new_cursor = result["data"]["exploreBotsConnection"]["edges"][-1]["cursor"]
            new_bots = [
                each["node"]
                for each in result["data"]["exploreBotsConnection"]["edges"]
            ]
            bots += new_bots
        logger.info("Succeed to explore bots")
        return bots[:count]

    # 创建bot
    @async_retry(3, "Failed to create bot")
    async def create_bot(
        self,
        handle: str,
        prompt: str,
        display_name: Optional[str] = None,
        base_model: str = "chinchilla",
        description: Optional[str] = "",
        intro_message: Optional[str] = "",
        api_key: Optional[str] = None,
        api_bot: Optional[bool] = False,
        api_url: Optional[str] = None,
        prompt_public: Optional[bool] = True,
        profile_picture_url: Optional[str] = None,
        linkification: Optional[bool] = False,
        markdown_rendering: Optional[bool] = True,
        suggested_replies: Optional[bool] = True,
        private: Optional[bool] = False,
        temperature: Optional[int] = None,
    ) -> None:
        result = await self.send_query(
            "CreateBotMain_poeBotCreate_Mutation",
            {
                "model": base_model,
                "displayName": display_name,
                "handle": handle,
                "prompt": prompt,
                "isPromptPublic": prompt_public,
                "introduction": intro_message,
                "description": description,
                "profilePictureUrl": profile_picture_url,
                "apiUrl": api_url,
                "apiKey": api_key,
                "isApiBot": api_bot,
                "hasLinkification": linkification,
                "hasMarkdownRendering": markdown_rendering,
                "hasSuggestedReplies": suggested_replies,
                "isPrivateBot": private,
                "temperature": temperature,
            },
        )

        data = result["data"]["poeBotCreate"]
        if data["status"] != "success":
            raise RuntimeError(f"Failed to create a bot with error: {data['status']}")
        # after creating, get the chatId (bot chat_data contains chatId) for using
        # when creating bot,the url_botname equals handle
        logger.info(f"Succeed to create a bot:{handle}")
        await self.get_bot(url_botname=handle)
        return

    # 编辑bot
    @async_retry(3, "Failed to edit bots")
    async def edit_bot(
        self,
        url_botname: str,
        handle: str = None,
        prompt: Optional[str] = None,
        display_name=None,
        base_model="",
        description="",
        intro_message="",
        api_key=None,
        api_url=None,
        is_private_bot=None,
        prompt_public=None,
        profile_picture_url=None,
        linkification=None,
        markdown_rendering=None,
        suggested_replies=None,
        temperature=None,
    ) -> None:
        bot_setting = await self.get_bot_setting(url_botname)

        result = await self.send_query(
            "EditBotMain_poeBotEdit_Mutation",
            {
                "baseBot": base_model or bot_setting["model"],
                "botId": bot_setting["botId"],
                "handle": handle or bot_setting["handle"],
                "displayName": display_name or bot_setting["displayName"],
                "prompt": prompt or bot_setting["promptPlaintext"],
                "isPromptPublic": prompt_public or bot_setting["isPromptPublic"],
                "introduction": intro_message or bot_setting["introduction"],
                "description": description or bot_setting["description"],
                "profilePictureUrl": profile_picture_url
                or bot_setting["profilePicture"],
                "apiUrl": api_url or bot_setting["apiUrl"],
                "apiKey": api_key or bot_setting["apiKey"],
                "hasLinkification": linkification or bot_setting["hasLinkification"],
                "hasMarkdownRendering": markdown_rendering
                or bot_setting["hasMarkdownRendering"],
                "hasSuggestedReplies": suggested_replies
                or bot_setting["hasSuggestedReplies"],
                "isPrivateBot": is_private_bot or bot_setting["isPrivateBot"],
                "temperature": temperature or bot_setting["temperature"],
            },
        )

        data = result["data"]["poeBotEdit"]
        if data["status"] != "success":
            raise RuntimeError(f"Failed to create a bot: {data['status']}")
        logger.info(f"Succeed to edit {url_botname}")
        return data

    # 删除bot
    @async_retry(3, "Failed to delete bots")
    async def delete_bot(self, url_botname: str) -> None:
        await self.ensure_botchat(url_botname)

        bot_id = self.bots[url_botname]["bot"]["botId"]

        try:
            if self.bots[url_botname]["bot"]["creator"]["id"] == self.user_id:
                response = await self.send_query(
                    "BotInfoCardActionBar_poeBotDelete_Mutation", {"botId": bot_id}
                )
            else:
                response = await self.send_query(
                    "BotInfoCardActionBar_poeRemoveBotFromUserList_Mutation",
                    {
                        "connections": [
                            "client:Vmlld2VyOjA=:__HomeBotSelector_viewer_availableBotsConnection_connection"
                        ],
                        "botId": bot_id,
                    },
                )
        except Exception:
            raise ValueError(
                f"Failed to delete bot {url_botname}. Make sure the bot exists and belongs to you."
            )
        if response["data"] is None and response["errors"]:
            raise ValueError(
                f"Failed to delete bot {url_botname} :{response['errors'][0]['message']}"  # noqa: E501
            )
        logger.info(f"Succeed to delete bot {url_botname}")
        del self.bots[url_botname]

    # 批量删除可用bot
    @async_retry(3, "Failed to delete available bots")
    async def delete_available_bots(
        self, count: Optional[int] = 2, del_all: Optional[bool] = False
    ):
        if not (del_all or count):
            raise TypeError(
                "Please provide at least one of the following parameters: del_all=<bool>, count=<int>"
            )

        async def del_bot(url_botname):
            try:
                await self.delete_bot(url_botname)
            except Exception as e:
                logger.error(
                    f"Failed to delete {url_botname} : {str(e)}. Make sure the bot belong to you."
                )

        tasks = []
        for bot, data in self.bots.items():
            if not data["bot"]["isSystemBot"]:
                tasks.append(asyncio.create_task(del_bot(bot)))
            else:
                logger.info("Can't delete SystemBot, skipped")
        await asyncio.gather(*tasks)
        logger.info("Succeed to delete bots")

    # 使用bot的chat的函数
    # 向一个新的会话发送消息
    async def send_message_to_new_chat(
        self, url_botname: str, question: str
    ) -> Tuple[int, int]:
        await self.ensure_botchat(url_botname)
        handle = self.bots[url_botname]["bot"]["nickname"]
        message_data = await self.send_query(
            "chatHelpersSendNewChatMessageMutation",
            {
                "bot": handle,
                "query": question,
                "source": {
                    "chatInputMetadata": {"useVoiceRecord": False},
                    "sourceType": "chat_input",
                },
                "sdid": self.sdid,
                "attachments": [],
            },
        )
        status = message_data["data"]["messageEdgeCreate"]["status"]
        if status == "reached_limit":
            raise Exception(f"Daily limit reached for {url_botname}.")
        elif status != "success":
            raise Exception(status)
        data = message_data["data"]["messageEdgeCreate"]["chat"]
        self.bots[url_botname]["chats"] = {
            data["chatCode"]: data,
            **self.bots[url_botname]["chats"],
        }
        logger.info(f"Succeed to send message to {url_botname}")

        return [
            a["node"]
            for a in data["messagesConnection"]["edges"]
            if a["node"]["author"] == "human"
        ][0]["messageId"], data["chatCode"]

    # 向一个原有的会话发送消息
    async def send_message_to_origin_chat(
        self,
        chat_code: str,
        url_botname: str,
        question: str,
        with_chat_break: bool = False,  # noqa: E501
    ) -> int:
        await self.ensure_botchat(url_botname, chat_code)
        async with self.chat_lock[chat_code]:
            # if chat_code not in self.bots[url_botname]["chats"]:
            bot = self.bots[url_botname]["bot"]["nickname"]
            message_data = await self.send_query(
                "chatHelpers_sendMessageMutation_Mutation",
                {
                    "chatId": self.bots[url_botname]["chats"][chat_code]["chatId"],
                    "bot": bot,
                    "query": question,
                    "source": {
                        "sourceType": "chat_input",
                        "chatInputMetadata": {"useVoiceRecord": False},
                    },
                    "withChatBreak": with_chat_break,
                    "clientNonce": generate_nonce(),
                    "sdid": self.sdid,
                    "attachments": [],
                },
            )
            if not message_data["data"]["messageEdgeCreate"]["message"]:
                if message_data["data"]["messageEdgeCreate"]["status"] == "no_access":
                    raise Exception("The bot doesn't exist or isn't accessible")
                else:
                    raise Exception(f"Daily limit reached for {url_botname}.")
            try:
                logger.info(f"Succeed to send message to {url_botname}")
                human_message = message_data["data"]["messageEdgeCreate"]["message"]
                human_message_id = human_message["node"]["messageId"]
                return human_message_id
            except TypeError:
                raise RuntimeError(
                    "Failed to extract human_message and human_message_id from response when asking: Unknown Error"
                )

    # 重新开始拉取会话信息
    async def restart_pulling_message(self):
        logger.info("restaring pulling message. ---")

        if self.wss_task and (not self.wss_task.done()):
            self.wss_task.cancel()

        @async_retry(3, "Failed to refresh wss channel")
        async def refresh_wss_channel():
            await self.get_channel_data()
            await self.subscribe()

        await refresh_wss_channel()

        self.wss_task = asyncio.create_task(self.put_message())

    # 向queue中放消息
    async def put_message(
        self,
    ):
        try:
            async with aiohttp.ClientSession(**self.session_args) as client:
                self.wss = await client.ws_connect(self.channel_url)
                while not self.wss.closed:
                    await asyncio.sleep(0.1)
                    try:
                        data = await self.wss.receive_json(timeout=3)
                        if (
                            data.get("error") == "missed_messages"
                            or data.get("message_type") == "refetchChannel"
                        ):
                            await self.wss.close()
                            await self.restart_pulling_message()
                            break
                        messages = [
                            json.loads(msg_str)
                            for msg_str in data.get("messages", "{}")
                        ]
                        for message in messages:
                            payload = message.get("payload", {})
                            chat_id = payload.get("unique_id").split(":")[-1]
                            subscription_name = payload.get("subscription_name")
                            if subscription_name == "messageAdded":
                                message = (payload.get("data", {})).get(
                                    "messageAdded", {}
                                )
                                self.queues[chat_id].put(
                                    Text(
                                        content=message.get("text"),
                                        msg_id=message.get("messageId"),
                                        finished=message.get("state") == "complete",
                                    )
                                )

                                for suggest_reply in message.get(
                                    "suggestedReplies", []
                                ):
                                    self.queues[chat_id].put(
                                        SuggestRely(
                                            content=suggest_reply,
                                            msg_id=message.get("messageId"),
                                        )
                                    )

                            elif subscription_name == "chatTitleUpdated":
                                title = (
                                    (payload.get("data", {})).get(
                                        "chatTitleUpdated", {}
                                    )
                                ).get("title", "")
                                self.queues[chat_id].put(ChatTiTleUpdate(content=title))
                            elif subscription_name == "messageCancelled":
                                self.queues[chat_id].put(TextCancel())
                            # else:
                            #     logger.info(
                            #         f"Unprocessed type: {subscription_name}"
                            #     )
                    except Exception:
                        pass
            await self.restart_pulling_message()
        except Exception as e:
            logger.warning(f"Failed to set up wss: {e}.\nRetrying...")
            await self.restart_pulling_message()

    # 分类别的询问生成器
    async def ask_stream_raw(
        self,
        url_botname: str,
        question: str,
        chat_code: str = None,
        with_chat_break: bool = False,
        suggest_able: bool = True,
    ):
        tasks = [
            asyncio.create_task(self.ensure_wss()),
            asyncio.create_task(self.ensure_botchat(url_botname)),
        ]
        await asyncio.gather(*tasks)

        suggest_able = suggest_able and self.bots[url_botname]["bot"].get(
            "hasSuggestedReplies", False
        )

        @async_retry(3, f"Failed to send msg to {url_botname}")
        async def send_msg(chat_code):
            async with self.bot_lock[url_botname]:
                if not chat_code:
                    human_msg_id, chat_code_ = await self.send_message_to_new_chat(
                        url_botname, question
                    )
                    return human_msg_id, ChatCodeUpdate(content=chat_code_)
                else:
                    human_msg_id = await self.send_message_to_origin_chat(
                        chat_code, url_botname, question, with_chat_break
                    )
                    return human_msg_id, None

        human_msg_id, data = await send_msg(chat_code)

        if data:
            chat_code = data.content
            yield data

        chat_id = str(self.bots[url_botname]["chats"][chat_code]["chatId"])

        if chat_id not in self.queues.keys():
            self.queues[chat_id] = queue.Queue()
        last_text = ""
        text_finished = False
        suggests = []
        timeout_time = 20
        lost_time = 10
        while True:
            await asyncio.sleep(0.1)

            if timeout_time <= 0:
                raise Exception("Timed out when getting answer from poe.com")
            if lost_time <= 0:
                logger.warning(
                    "Failed to get enough suggest replys from poe.com.Early return."
                )
                break

            try:
                data = self.queues[chat_id].get(timeout=2)
                if isinstance(data, Text):
                    if data.msg_id > human_msg_id:
                        self.bot_crt_msg_id[chat_code] = data.msg_id
                        timeout_time = 20
                        yield Text(
                            content=data.content[len(last_text) :],
                            msg_id=data.msg_id,
                            finished=data.finished,
                        )
                        last_text = data.content
                        if data.finished:
                            text_finished = True
                            if not suggest_able:
                                break
                elif isinstance(data, TextCancel):
                    break
                elif isinstance(data, SuggestRely) and suggest_able:
                    if data.msg_id > human_msg_id:
                        if data not in suggests:
                            suggests.append(data)
                            lost_time = 10
                            yield data
                            if len(suggests) >= 3:
                                break
                        else:
                            continue
                elif isinstance(data, ChatTiTleUpdate):
                    yield data
            except Exception:
                timeout_time -= 1
                if text_finished:
                    lost_time -= 1
                elif not last_text:
                    await asyncio.sleep(3)
        if chat_code in self.bot_crt_msg_id.keys():
            del self.bot_crt_msg_id[chat_code]

    # 纯文本的询问生成器
    async def ask_stream(
        self,
        url_botname: str,
        question: str,
        chat_code: str = None,
        with_chat_break: bool = False,
        suggest_able: bool = True,
    ):
        suggests = []
        async for data in self.ask_stream_raw(
            url_botname, question, chat_code, with_chat_break, suggest_able
        ):
            if isinstance(data, Text):
                yield data.content
            elif suggest_able:
                if isinstance(data, SuggestRely):
                    suggests.append(data)
        if suggests:
            yield "\n\nSuggest Replys:\n"
            index = 1
            for suggest in suggests:
                yield f"{index}: {suggest}\n"
                index += 1

    # 发送一个终止回答生成的请求
    async def stop_chat(self, chat_code: str):
        if chat_code not in self.bot_crt_msg_id.keys():
            raise Exception("The bot is not generating answer.")
        message_id = self.bot_crt_msg_id[chat_code]
        await self.send_query(
            "chatHelpers_messageCancel_Mutation",
            {"messageId": int(message_id), "textLength": 0, "linkifiedTextLength": 0},
        )
        logger.info("Succeed to stop chat generating.")

    # 发送一个chat break来清除会话的历史记忆
    async def send_chat_break(self, url_botname: str, chat_code: str) -> None:
        await self.ensure_botchat(url_botname, chat_code)

        await self.send_query(
            "chatHelpers_addMessageBreakEdgeMutation_Mutation",
            {
                "connections": [
                    f"client:{self.bots[url_botname]['chats'][chat_code]['id']}:__ChatMessagesView_chat_messagesConnection_connection"
                ],
                "chatId": self.bots[url_botname]["chats"][chat_code]["chatId"],
            },
        )
        logger.info(f"Succeed to chat break to {url_botname}")
        return

    # 基本操作函数
    # 发送query请求
    @async_retry(3, "Failed to send query")
    async def send_query(self, query_name: str, variables: dict) -> Union[dict, None]:
        """poe.com的通用的query发送"""
        data = generate_data(query_name, variables)
        base_string = data + self.formkey + self.salt
        query_headers = {
            **self.headers,
            "content-type": "application/json",
            "poe-tag-id": hashlib.md5(base_string.encode()).hexdigest(),
        }

        async with aiohttp.ClientSession(**self.session_args) as client:
            response = await client.post(GQL_URL, data=data, headers=query_headers)
            resp = await response.text()
            json_data = json.loads(resp)
            if (
                "success" in json_data.keys()
                and not json_data["success"]
                or json_data["data"] is None
            ):
                detail_error = Exception(json_data["errors"][0]["message"])
                raise detail_error
            else:
                return json_data

    async def subscribe(self):
        try:
            await self.send_query(
                "subscriptionsMutation",
                {
                    "subscriptions": [
                        {
                            "subscriptionName": "messageAdded",
                            "query": None,
                            "queryHash": "6d5ff500e4390c7a4ee7eeed01cfa317f326c781decb8523223dd2e7f33d3698",
                        },
                        {
                            "subscriptionName": "messageCancelled",
                            "query": None,
                            "queryHash": "dfcedd9e0304629c22929725ff6544e1cb32c8f20b0c3fd54d966103ccbcf9d3",
                        },
                        {
                            "subscriptionName": "messageDeleted",
                            "query": None,
                            "queryHash": "91f1ea046d2f3e21dabb3131898ec3c597cb879aa270ad780e8fdd687cde02a3",
                        },
                        {
                            "subscriptionName": "viewerStateUpdated",
                            "query": None,
                            "queryHash": "ee640951b5670b559d00b6928e20e4ac29e33d225237f5bdfcb043155f16ef54",
                        },
                        {
                            "subscriptionName": "messageLimitUpdated",
                            "query": None,
                            "queryHash": "d862b8febb4c058d8ad513a7c118952ad9095c4ec0a5471540133fc0a9bd3797",
                        },
                        {
                            "subscriptionName": "chatTitleUpdated",
                            "query": None,
                            "queryHash": "740e2c7ab27297b7a8acde39a400b932c71beb7e9b525280fc99c1639f1be93a",
                        },
                    ]
                },
            )
            logger.info("Succeed to subscribe")
        except Exception as e:
            raise Exception(
                "Failed to subscribe by sending SubscriptionsMutation"
            ) from e

    # 确保存在bot和chat
    async def ensure_botchat(self, url_botname: str, chat_code: str = "", load=True):
        """确保bot或chat存在"""
        if url_botname not in self.bot_lock.keys():
            self.bot_lock[url_botname] = asyncio.Lock()
        if chat_code and (chat_code not in self.chat_lock.keys()):
            self.chat_lock[chat_code] = asyncio.Lock()
        tasks = []
        if load:
            if url_botname and not self.bots.get(url_botname, {}).get("bot", {}):
                tasks.append(asyncio.create_task(self.get_bot(url_botname)))
            if (url_botname and chat_code) and not self.bots.get(url_botname, {}).get(
                "chats", {}
            ).get(chat_code, {}):
                tasks.append(asyncio.create_task(self.get_chat(url_botname, chat_code)))
            if tasks:
                await asyncio.gather(*tasks)
        else:
            if url_botname not in self.bots.keys():
                self.bots[url_botname] = {"bot": {}, "chats": {}}
            if "chats" not in self.bots[url_botname].keys():
                self.bots[url_botname]["chats"] = {}
            if "bot" not in self.bots[url_botname].keys():
                self.bots[url_botname]["bot"] = {}
            if chat_code and chat_code not in self.bots[url_botname]["chats"].keys():
                self.bots[url_botname]["chats"][chat_code] = {}

    async def ensure_wss(self):
        def is_wss_well():
            return (
                not self.wss
                or self.wss.closed
                or not self.wss_task
                or self.wss_task.done()
            )

        if is_wss_well():
            await self.restart_pulling_message()

        async def maintain_wss():
            retry = 5
            while is_wss_well() and retry > 0:
                retry -= 1
                await asyncio.sleep(1)
            if retry <= 0:
                await self.restart_pulling_message()
                return False
            else:
                return True

        well = await maintain_wss()
        if not well:
            well = await maintain_wss()
            if not well:
                raise RuntimeError("Failed to maintain the wss")
