import asyncio
import hashlib
import json
import random
import re
import time
import uuid
from typing import List, Union, AsyncGenerator, Optional, Tuple

import aiohttp
from aiohttp_socks import ProxyConnector
from loguru import logger

from .type import Text, ChatTiTleUpdate, SuggestRely, ChatCodeUpdate
from .util import (
    HOME_URL,
    GQL_URL,
    SETTING_URL,
    CONST_NAMESPACE,
    generate_data,
    generate_nonce,
)


class Poe_Client:
    def __init__(self, p_b: str, formkey: str, proxy: Optional[str] = ""):
        self.channel_url: str = ""
        self.channel_use_time = 0
        self.channel_last_use_time = time.time()
        self.bots: dict = {}
        self.formkey: str = formkey
        self.next_data: dict = {}
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
        result = {}
        for bot, data in self.bots.items():
            result[bot] = []
            for chat in data["chats"]:
                result[bot].append(chat)
        return result

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

    async def get_basedata(self) -> None:
        """
        This function fetches the basic data from the HOME_URL and sets various attributes of the object.

        Raises:
            Raises an Exception if it fails to get the base data.
            Raises a ValueError if it fails to extract 'next_data', 'viewer', 'user_id', or 'formkey' from the response.
        """
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
            self.next_data = json.loads(json_text)
        except Exception as e:
            raise ValueError("Failed to extract 'next_data' from the response.") from e

        """extract data from next_data"""
        try:
            self.viewer = self.next_data["props"]["initialData"]["data"]["pageQuery"][
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

    async def get_channel_data(self) -> None:
        """
        This function fetches the channel data from the SETTING_URL and sets the 'tchanneldata' attribute of the object.

        Raises:
            Raises a ValueError if it fails to extract the channel data from the response.
        """
        try:
            async with aiohttp.ClientSession(**self.session_args) as client:
                response = await client.get(SETTING_URL)
                data = await response.text()
                json_data = json.loads(data)
                self.tchannel_data = json_data["tchannelData"]
                self.headers["Poe-Tchannel"] = self.tchannel_data["channel"]
                self.channel_url = f'https://{self.ws_domain}.tch.{self.tchannel_data["baseHost"]}/up/{self.tchannel_data["boxName"]}/updates?min_seq={self.tchannel_data["minSeq"]}&channel={self.tchannel_data["channel"]}&hash={self.tchannel_data["channelHash"]}'
                logger.info("succeed to get channel data")
        except Exception as e:
            raise ValueError("Failed to extract tchannel from response.") from e

    async def create(self, pre_load: bool = True):
        """
        :param pre_load: whether to pre_load all the available bots and their data
        This function initializes the Async_Poe_Client instance by fetching the base data, channel data, and bot data,
        and then subscribing to the channel.

        Returns:
            Returns the initialized instance of the Async_Poe_Client.

        Note:
            This function should be called after creating a new Async_Poe_Client instance to ensure that all necessary data is fetched and set up.
        """
        logger.info("Creating client -----")
        retry = 3
        while retry >= 0:
            try:
                await self.get_basedata()
                break
            except Exception as e:
                retry -= 1
                if retry == 0:
                    raise e
        if pre_load:
            await self.get_available_bots(get_all=True)
            await self.load_all_bots()
        logger.info("Succeed to create async_poe_client instance")
        return self

    async def get_botdata(self, url_botname: str) -> dict:
        """
        This function gets the chat data of the bot include chat history.

        Args:
            url_botname (str): The name of the bot used in the URL to fetch the bot's chat data.

        Returns:
            Returns the chat data of the bot.

        Raises:
            Raises a ValueError exception if it fails to get the chat data.
        """

        retry = 3
        error = Exception("Unknown error")
        while retry > 0:
            try:
                bot_task = asyncio.ensure_future(
                    (
                        lambda: self.send_query(
                            "BotLandingPageQuery", {"botHandle": url_botname}
                        )
                    )()
                )
                chats_task = asyncio.ensure_future(
                    (
                        lambda: self.send_query(
                            "chatsHistoryPageQuery",
                            {"handle": url_botname, "useBot": True},
                        )
                    )()
                )
                await asyncio.gather(bot_task, chats_task)

                bot = bot_task.result()["data"]["bot"]
                chats = {
                    str(chat["node"]["chatCode"]): chat["node"]
                    for chat in chats_task.result()["data"]["filteredChats"]["edges"]
                }

                self.bots[url_botname] = {"bot": bot, "chats": chats}
                return self.bots[url_botname]
            except Exception as e:
                error = e
                retry -= 1
        raise ValueError(f"Failed to get bot chat_data of {url_botname}") from error

    async def get_bot_info(self, url_botname: str) -> dict:
        """
        This function gets the bot's setting information.

        Args:
            url_botname (str): The name of the bot used in the URL to fetch the bot's information.

        Returns:
            Returns a dictionary containing the bot's information.

        Raises:
            Raises a ValueError exception if it fails to get the bot's info.
        """
        try:
            data = await self.send_query(
                "editBotIndexPageQuery", {"botName": url_botname}
            )
            return data["data"]["bot"]
        except Exception as e:
            raise ValueError(
                f"Failed to get bot info from {url_botname}. Make sure the bot is not deleted"
            ) from e

    async def load_all_bots(self) -> None:
        """
        This function fetches and saves the chat data of all bots in client.bots.

        Raises:
            Raises a RuntimeError exception if it fails to get any bots, or if the token is invalid.
        """

        tasks = []
        for bot in list(self.bots.keys()):
            task = asyncio.create_task(self.get_botdata(bot))
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def send_query(self, query_name: str, variables: dict) -> Union[dict, None]:
        """
        A general-purpose function used to send queries to a server. This function is primarily used by other functions in the program.

        Args:
            query_name (str): The name of the query that should be sent.
            variables (dict): A dictionary of the variables that should be included in the message.

        Returns:
            Returns the JSON response data from the server if the query is successful.

        Raises:
            Raises an Exception if the query fails after 5 retries.
        """

        data = generate_data(query_name, variables)
        base_string = data + self.formkey + self.salt
        query_headers = {
            **self.headers,
            "content-type": "application/json",
            "poe-tag-id": hashlib.md5(base_string.encode()).hexdigest(),
        }
        retry = 5
        detail_error = Exception("unknown error")
        while retry:
            try:
                async with aiohttp.ClientSession(**self.session_args) as client:
                    response = await client.post(
                        GQL_URL, data=data, headers=query_headers
                    )
                    resp = await response.text()
                    json_data = json.loads(resp)
                    if (
                        "success" in json_data.keys()
                        and not json_data["success"]
                        or json_data["data"] is None
                    ):
                        detail_error = Exception(json_data["errors"][0]["message"])
                        raise detail_error
                    return json_data
            except Exception as e:
                detail_error = e
                logger.error(
                    f"Failed to sending query:{query_name},error:{detail_error}. (retry: {retry}/5)"
                )
                retry -= 1
        raise Exception(
            f"Too much error when sending query:{query_name},error:{detail_error}"
        ) from detail_error

    async def subscribe(self):
        """
        This function is used to simulate a human user opening the website by subscribing to certain mutations.

        Raises:
            Raises an Exception if it encounters a failure while sending the SubscriptionsMutation.
        """
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
        """
        This function is used to create a new bot with the specified configuration.

        Args:
            handle (str): The handle for the new bot which should be unique.
            prompt (str): The prompt for the new bot.
            display_name (str, optional): The display name for the new bot. If not provided, it will be set to None.
            base_model (str, optional): The base model for the new bot. Default is "chinchilla".
            description (str, optional): The description for the new bot. If not provided, it will be set to an empty string.
            intro_message (str, optional): The introduction message for the new bot. If not provided, it will be set to an empty string.
            api_key (str, optional): The API key for the new bot. If not provided, it will be set to None.
            api_bot (bool, optional): Whether the new bot is an API bot. Default is False.
            api_url (str, optional): The API URL for the new bot. If not provided, it will be set to None.
            prompt_public (bool, optional): Whether to set the bot's prompt to public. Default is True.
            profile_picture_url (str, optional): The profile picture URL for the new bot. If not provided, it will be set to None.
            linkification (bool, optional): Whether to enable linkification. Default is False.
            markdown_rendering (bool, optional): Whether to enable markdown rendering. Default is True.
            suggested_replies (bool, optional): Whether to enable suggested replies. Default is False.
            private (bool, optional): Whether to set the bot as private. Default is False.
            temperature (int, optional): The temperature setting for the new bot. If not provided, it will be set to None.

        Returns:
            Returns a dictionary containing information about the creation result.

        Raises:
            Raises a RuntimeError exception if the creation fails.

        Note:
            When creating a new bot, you only need to provide the `handle` and `prompt`. All other parameters are optional and will be set to their default values if not provided.
            Please ensure that the `handle` is unique and does not conflict with the handles of existing bots.
        """
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
        await self.get_botdata(url_botname=handle)
        return

    async def edit_bot(
        self,
        url_botname: str,
        handle: str = None,
        prompt: Optional[str] = None,
        display_name=None,
        base_model="chinchilla",
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
        """
        This function is used to edit the configuration of an existing bot.

        Args:
            url_botname (str): The URL name of the bot to be edited.
            handle (str, optional): The new handle for the bot. If not provided, it will remain unchanged.
            prompt (str, optional): The new prompt for the bot. If not provided, it will remain unchanged.
            display_name (str, optional): The new display name for the bot. If not provided, it will remain unchanged.
            base_model (str, optional): The new base model for the bot. If not provided, it will remain unchanged.
            description (str, optional): The new description for the bot. If not provided, it will remain unchanged.
            intro_message (str, optional): The new introduction message for the bot. If not provided, it will remain unchanged.
            api_key (str, optional): The new API key for the bot. If not provided, it will remain unchanged.
            api_url (str, optional): The new API URL for the bot. If not provided, it will remain unchanged.
            is_private_bot (bool, optional): Whether to set the bot to private. If not provided, it will remain unchanged.
            prompt_public (bool, optional): Whether to set the bot's prompt to public. If not provided, it will remain unchanged.
            profile_picture_url (str, optional): The new profile picture URL for the bot. If not provided, it will remain unchanged.
            linkification (bool, optional): Whether to enable linkification. If not provided, it will remain unchanged.
            markdown_rendering (bool, optional): Whether to enable markdown rendering. If not provided, it will remain unchanged.
            suggested_replies (bool, optional): Whether to enable suggested replies. If not provided, it will remain unchanged.
            temperature (float, optional): The new temperature setting for the bot. If not provided, it will remain unchanged.

        Returns:
            Returns a dictionary containing information about the edit result.

        Raises:
            Raises a RuntimeError exception if the edit fails.

        Note:
            The `url_botname` parameter is the original URL name of the bot that you want to edit. This is required to identify which bot's configuration you are targeting to change.
            All other parameters represent the new values you want to set for the bot's configuration. If a parameter is not provided, the corresponding configuration of the bot will remain unchanged.
        """
        botinfo = await self.get_bot_info(url_botname)

        result = await self.send_query(
            "EditBotMain_poeBotEdit_Mutation",
            {
                "baseBot": base_model or botinfo["model"],
                "botId": botinfo["botId"],
                "handle": handle or botinfo["handle"],
                "displayName": display_name or botinfo["displayName"],
                "prompt": prompt or botinfo["promptPlaintext"],
                "isPromptPublic": prompt_public or botinfo["isPromptPublic"],
                "introduction": intro_message or botinfo["introduction"],
                "description": description or botinfo["description"],
                "profilePictureUrl": profile_picture_url or botinfo["profilePicture"],
                "apiUrl": api_url or botinfo["apiUrl"],
                "apiKey": api_key or botinfo["apiKey"],
                "hasLinkification": linkification or botinfo["hasLinkification"],
                "hasMarkdownRendering": markdown_rendering
                or botinfo["hasMarkdownRendering"],
                "hasSuggestedReplies": suggested_replies
                or botinfo["hasSuggestedReplies"],
                "isPrivateBot": is_private_bot or botinfo["isPrivateBot"],
                "temperature": temperature or botinfo["temperature"],
            },
        )

        data = result["data"]["poeBotEdit"]
        if data["status"] != "success":
            raise RuntimeError(f"Failed to create a bot: {data['status']}")
        logger.info(f"Succeed to edit {url_botname}")
        return data

    async def explore_bots(
        self, count: int = 50, explore_all: bool = False
    ) -> List[dict]:
        """
        Asynchronously explore and fetch a specified number of third party bots.

        Args:
            count (int, optional): The number of bots to explore. Defaults to 50.
            explore_all (bool, optional): Whether to explore all third party bots. Defaults to False
        Returns:
            List[dict]: A list of dictionaries representing the explored bots.
                        Each dictionary represents a bot and includes details
                        about the bot. If fewer bots are found than requested,
                        the function will return a list of the found bots.

        Raises:
            Any exceptions raised by `self.send_query()` will be propagated.
        """
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

    async def create_new_chat(self, url_botname: str, question: str) -> Tuple[int, int]:
        """
        创建一个bot的新的对话,返回human_msg_id和chat_code
        """
        if url_botname not in self.bots.keys():
            self.bots[url_botname] = await self.get_botdata(url_botname)
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

    async def send_message_to_chat(
        self,
        chat_code: str,
        url_botname: str,
        question: str,
        with_chat_break: bool = False,  # noqa: E501
    ) -> int:
        """
        Sends a message to a specified bot and retrieves the message ID of the sent message.

        Parameters:
            chat_code (str): The unique identifier of a conservation with certain bot
            url_botname (str): The unique identifier of the bot to which the message is to be sent.
            question (str): The message to be sent to the bot.
            with_chat_break: send chat break after ask
        Returns:
            int: The message ID of the sent message.

        Raises:
            Exception: If the daily limit for messages to the bot has been reached.
            RuntimeError: If there is an error in extracting the message ID from the response.

        Note:
            This function sends a message to the bot but does not retrieve the bot's response. The 'ask_stream_raw' or 'ask_stream' function should be used to send and retrieve the bot's response.

        """
        if url_botname not in self.bots.keys():
            self.bots[url_botname] = await self.get_botdata(url_botname)
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

    async def ask_stream_raw(
        self,
        url_botname: str,
        question: str,
        chat_code: str = None,
        with_chat_break: bool = False,
        suggest_able: bool = True,
    ) -> AsyncGenerator:
        """
        Asynchronously sends a question to a specified bot and yields the bot's responses as they arrive.

        Args:
            url_botname (str): The unique identifier of the bot to which the question is to be sent.
            chat_code (str): The unique identifier of the conservation with the bot. If not provided, it will generate a new chat automatically.
            question (str): The question to be sent to the bot.
            with_chat_break (bool, optional): If set to True, a chat break will be sent before the question, clearing the bot's conversation memory. Default is False.
            suggest_able (bool, optional): If set to True, suggested replies from the bot will be included in the responses. Default is False.

        Returns:
            AsyncGenerator[Any]: An asynchronous generator that yields the bot's raw responses as they arrive.

        Raises:
            Exception: If there is a failure in receiving messages from the bots.
        """
        if url_botname not in self.bots.keys():
            await self.get_botdata(url_botname)
        suggest_able = (
            suggest_able and self.bots[url_botname]["bot"]["hasSuggestedReplies"]
        )
        if (
            self.channel_use_time % 3 == 0
            or time.time() - self.channel_last_use_time >= 360
        ):  # noqa: E501
            await self.get_channel_data()
            await self.subscribe()

        self.channel_use_time += 1
        self.channel_last_use_time = time.time()

        retry = 3
        error = "Unknown error"
        while retry >= 0:
            if retry == 0:
                raise error
            try:
                if not chat_code:
                    human_message_id, chat_code = await self.create_new_chat(
                        url_botname, question
                    )
                    yield ChatCodeUpdate(content=chat_code)
                else:
                    human_message_id = await self.send_message_to_chat(
                        chat_code, url_botname, question, with_chat_break
                    )
                break
            except Exception as e:
                retry -= 1
                error = e
                pass

        async with aiohttp.ClientSession(**self.session_args) as client:
            self.bots[url_botname]["Suggestion"] = []
            retry = 15
            last_text = ""
            got_suggest_replys = []
            got_titles = []
            text_finished = False
            target_message_id = None
            suggest_lost_times = 10
            while retry >= 0 and suggest_lost_times >= 0:
                response = await client.get(self.channel_url)
                data = await response.json()
                messages = [
                    json.loads(msg_str) for msg_str in data.get("messages", "{}")
                ]
                got_new_text = False
                for message in messages:
                    payload = message.get("payload", {})
                    if payload.get("subscription_name") == "messageAdded":
                        message = (payload.get("data", {})).get("messageAdded", {})
                        plain_text = message.get("text")
                        if plain_text == question:
                            continue
                        if message and message.get("state") == "incomplete":
                            if (
                                message.get("messageId") < human_message_id
                                or plain_text == last_text
                                or (
                                    target_message_id is not None
                                    and message.get("messageId") != target_message_id
                                )
                            ):
                                continue
                            else:
                                target_message_id = message.get("messageId")
                                got_new_text = True
                                retry = 15
                                yield Text(content=plain_text[len(last_text) :])
                                last_text = plain_text
                        else:
                            if not text_finished:
                                text_finished = Text
                                yield Text(
                                    content=message.get("text")[len(last_text) :]
                                )

                            if not suggest_able:
                                return

                            suggest_replys = message.get("suggestedReplies", [])
                            got_new_reply = False
                            for suggest_reply in suggest_replys:
                                if suggest_reply not in got_suggest_replys:
                                    suggest_lost_times = 10
                                    got_suggest_replys.append(suggest_reply)
                                    got_new_reply = True
                                    yield SuggestRely(content=suggest_reply)
                            if len(suggest_replys) >= 3:
                                return
                            if suggest_lost_times <= 0:
                                logger.error(
                                    "Poe didn't send enough Suggest Reply in time. Early Returned."
                                )
                                return
                            if not got_new_reply:
                                await asyncio.sleep(1)
                                suggest_lost_times -= 1
                    elif payload.get("subscription_name") == "chatTitleUpdated":
                        title = (
                            (payload.get("data", {})).get("chatTitleUpdated", {})
                        ).get(
                            "title", ""
                        )  # noqa: E501
                        if title and title not in got_titles:
                            got_titles.append(title)
                            yield ChatTiTleUpdate(content=title)
                if not got_new_text:
                    retry -= 1
                    await asyncio.sleep(1)
            raise Exception("Failed to get message from poe in time.")

    async def ask_stream(
        self,
        url_botname: str,
        question: str,
        chat_code: str = None,
        with_chat_break: bool = False,
        suggest_able: bool = True,
    ) -> AsyncGenerator:
        suggest_replys = []

        async for data in self.ask_stream_raw(
            url_botname=url_botname,
            question=question,
            chat_code=chat_code,
            with_chat_break=with_chat_break,
            suggest_able=suggest_able,
        ):
            if isinstance(data, Text):
                yield str(data)
            elif isinstance(data, SuggestRely):
                suggest_replys.append(str(data))
                if len(suggest_replys) == 1:
                    yield "\nSuggest Replys:\n"
                yield f"{len(suggest_replys)}: {data}\n"

    async def send_chat_break(self, url_botname: str, chat_code: str) -> None:
        """
        Asynchronously sends a chat break to a specified bot, effectively clearing the bot's conversation memory.

        Parameters:
            url_botname (str): The unique identifier of the bot to which the chat break is to be sent.
            chat_code (str): The unique identifier of the chat with the bot
        Returns:
            None

        Note:
            This function clears the language model's conversation memory for the specified bot, so it should be used with caution.

        """
        if url_botname not in self.bots.keys():
            await self.get_botdata(url_botname)
        if chat_code not in self.bots[url_botname]["chats"].keys():
            await self.get_botdata(url_botname)
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

    async def get_available_bots(
        self, count: Optional[int] = 25, get_all: Optional[bool] = False
    ) -> dict:  # noqa: E501
        """
        Get own available bots .

        Args:
            count (int, optional): The number of bots to get.
            get_all (bool, optional): Whether to get all bots.

        Raises:
            TypeError: If neither 'get_all' nor 'count' parameter is provided.

        Returns:
            None
        """
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

    async def delete_chat_by_chat_id(self, chat_id: str):
        """
        delete chat by chatId .

        Args:
            chat_id (int, optional): The chat_id to delete.

        Returns:
            None
        """
        await self.send_query("useDeleteChat_deleteChat_Mutation", {"chatId": chat_id})
        logger.info(f"succeed to delete chat:{chat_id}")

    async def delete_chat_by_chat_code(self, chat_code: str):
        """
        delete chat by chat_code .

        Args:
            chat_code (int, optional): The chat_code to delete.

        Returns:
            None
        """
        result = {
            k: v for each in list(self.bots.values()) for k, v in each["chats"].items()
        }
        if chat_code not in result.keys():
            await self.get_available_bots(get_all=True)
            await self.load_all_bots()
        result = {
            k: v for each in list(self.bots.values()) for k, v in each["chats"].items()
        }
        await self.delete_chat_by_chat_id(result[chat_code]["chatId"])

    async def delete_chat_by_count(
        self, url_botname: str, count: int = 20, del_all: bool = False
    ):
        """
        delete chats by url_botname and count .

        Args:
            url_botname (str): The chats of which bot to delete.
            count (int, optional): the count of the chats to delete.
            del_all (bool, optional): whether to delete all the chats with the bot.
        Returns:
            None
        """
        await self.get_botdata(url_botname)

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

    async def delete_bot(self, url_botname: str) -> None:
        """
        This function is used to edit the configuration of an existing bot.

        Args:
            url_botname (str): The URL name of the bot to be edited.

        Returns:
            Returns None.

        Raises:
            Raises a ValueError exception if error occurs when sending query or the status is not 'success'.

        Note:
            This function will delete the bot permanently, so caution.
        """
        if url_botname not in self.bots.keys():
            self.bots[url_botname] = await self.get_botdata(url_botname)

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

    async def delete_available_bots(
        self, count: Optional[int] = 2, del_all: Optional[bool] = False
    ):
        """
        Asynchronously deletes some or all user available bots.

        Args:
            count (int, optional): The number of bots to delete.
            del_all (bool, optional): Whether to delete all bots.
        Raises:
            TypeError: If neither 'del_all' nor 'count' parameter is provided

        Returns:
            None

        Note:
            Be careful while using this function as it will permanently remove the bots.
            Delete all bots may take a long time depends on the num of your bots.
        """
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

    async def get_chat_history(
        self, url_botname: str, chat_code: str, count: int = 25, get_all: bool = False
    ):
        if url_botname not in self.bots.keys():
            await self.get_botdata(url_botname)
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
