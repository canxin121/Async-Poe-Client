# User Guide

[中文版本](README_zh_CN.md)

This is a guide on how to use the `async-poe-Client` library. Before starting, make sure you've installed this library.

```
pip install async-poe-client
```

## Contents

- [QA](#qa)
- [Step 1: Import the library and create a Poe_Client object](#step-1-import-the-library-and-create-a-poeclient-object)
- [Step 2: Use Poe_Client](#step-2-use-poeclient)
    - [1. Get Account Subscription Information](#1-get-the-subscription-information-of-the-account)
    - [2. Create a Bot](#2-create-a-bot)
    - [3. Edit a Bot’s Settings](#3-edit-a-bots-settings)
    - [4. Delete a Bot](#4-delete-a-bot)
    - [5. Chat with a Bot](#5-chat-with-a-bot)
        - [(1). Use websockets and httpx supported functions for streaming output and suggested replies](#1-using-websockets-and-httpx-support-for-streaming-output-and-suggested-replies)
        - [(2). Use httpx only supported functions without suggested replies and streaming output](#2-function-that-only-uses-httpx-and-does-not-support-suggested-replies-and-streaming-output)
    - [6. Delete a Bot's Dialogue Memory, Reset Conversation (This won't delete messages in chat history)](#6-deleting-a-bots-dialogue-memory-resetting-the-dialogue-this-does-not-delete-messages-in-the-chat-history)
    - [7. Get your Available Bots](#7-get-your-own-available-bots)
    - [8. Bulk Delete your Available Bots](#8-bulk-delete-your-available-bots)
    - [9. Get partial data or full settings of a bot](#9-get-partial-data-or-full-settings-of-a-bot)
    - [10. Get Chat History (Chat Messages)](#10-get-chat-history-chat-messages)
    - [11. Delete Chat History (Chat Messages)](#11-delete-chat-history-chat-messages)
        - [(1). Delete Chat History with a Certain Bot](#1-delete-chat-history-with-a-certain-bot)
        - [(2). Delete All Chat History with All Bots](#2-delete-all-chat-history-with-all-bots)
    - [12. Get Bots Created by Others (Bots in Explore Page)](#12-get-bots-created-by-others-bots-in-explore-page)
# QA:

- 1.What is url_botname? -> When using a certain bot on poe, it is the name of the bot in the link ("ChatGPT"
  in "[https://poe.com/ChatGPT ↗](https://poe.com/ChatGPT)").  
  The relationship between this url_botname and other names can be understood as:  
    1. For the system's built-in bots, the name of the bot you see on the poe web page and the url_name are always
       equal (but neither equals the handle).
    2. For bots you create, url_name = handle. If display_name is set, the name you see on the web page is display_name;
       if not set, you see url_name (handle).
       However, there are special cases where the handle does not follow the above rules, such as the handle of all bots
       obtained using get_available_bots always equals url_botname.

## Step 1: Import the library and create a Poe_Client object

Before you can use any functionality of the `Poe_Client` library, you first need to import the library and create
a `Poe_Client` object. You need to pass the `p_b token` to the constructor of `Poe_Client`, and then call the `create`
method to initialize it. Here is an example:

```python
from async_poe_client import Poe_Client

poe_client = await Poe_Client("your p_b token").create()
```

Here, `"your p_b token"` should be replaced with your actual p_b token.

## Step 2: Use Poe_Client

After creating the `Poe_Client`, you can use it to perform a lot of operations.

---

### 1. Get the subscription information of the account

You can get this directly by accessing the property value

```python
print(poe_client.subscription)
```

This will return a dictionary formatted subscription information.

---

### 2. Create a bot

Function: create_bot()

Parameters:

- `handle: str` - The name of the new bot, which must be a string. This name must be unique throughout poe.com, and it
  should not be the same as any other person's name.
- `prompt: str = ""` - The preset personality of the new bot. This is an optional string, with the default value being
  an empty string.
- `display_name: Optional[str] = `None`` - The display name of the new bot. This is an optional string, with a default
  value of `None`. If not provided, it will display the handle.
- `base_model: str = "chinchilla"` - The model used by the new bot. This is an optional string. The choices include: "
  chinchilla" (ChatGPT) or "a2" (Claude). If subscribed, you can use "beaver" (ChatGPT4) or "a2_2" (Claude-2-100k).
- `description: str = ""` - The description of the new bot. This is an optional string, with the default value being an
  empty string.
- `intro_message: str = ""` - The introductory information of the new bot. This is an optional string. If it is an empty
  string, then the bot will not have any introductory information.
- `prompt_public: bool = True` - Whether the preset personality should be publicly visible. This is an optional boolean,
  with the default value being True.
- `profile_picture_url: Optional[str] = `None`` - The URL of the bot's profile picture. This is an optional string, with
  the default value being `None`. Using this library does not actually allow you to upload custom images.
- `linkification: bool = False` - Whether the bot should convert some text in the response into clickable links. This is
  an optional boolean, with the default value being False.
- `markdown_rendering: bool = True` - Whether the bot's response should enable markdown rendering. This is an optional
  boolean, with the default value being True.
- `suggested_replies: bool = True` - Whether the bot should suggest possible replies after each response. This is an
  optional boolean, with the default value being False.
- `private: bool = False` - Whether the bot should be private. This is an optional boolean, with the default value being
  False.
- `temperature: Optional[float] = `None`` - The temperature of the new bot. This is an optional float, with the default
  value being `None`.

If you want the new bot to use your own API (you can get the official poe tutorial for
accessing [here ↗](https://github.com/poe-platform/api-bot-tutorial)), please use the following parameters:

- `api_bot = False` - Whether the bot is your own API bot.
- `api_key = `None`` - The API key of the new bot.
- `api_url = `None`` - The API URL of the new bot.
  Return value: `None`

The simplest usage is shown below. You only need to pass the handle and prompt to create a bot.

```python
await poe_client.create_bot(handle="testbotcx1", prompt="a ai assistant")
```

---

### 3. Edit a Bot’s Settings

Function: `edit_bot()`

Parameters:

Note that only `url_botname` is the original name of the bot, the rest are parameters to be modified. If not passed, the
parameter will remain unchanged.

- `url_botname: str` - The url_name of the bot to be modified. This must be a string.
- `handle: Optional[str]` - The name of the bot. This must be a string and must be unique across poe.com, i.e., it
  should not be the same as other bots.
- `prompt: Optional[str] = ""` - The preset personality of the bot. This is an optional string, defaulting to an empty
  string.
- `display_name: Optional[str] = None` - The display name of the bot. This is an optional string, defaulting to `None`.
  If not passed, the handle will be displayed.
- `base_model: Optional[str] = "chinchilla"` - The model used by the bot. This is an optional string. Options include: "
  chinchilla" (ChatGPT) or "a2" (Claude). If subscribed, you can use "beaver" (ChatGPT4) or "a2_2" (Claude-2-100k).
- `description: Optional[str] = ""` - The description of the bot. This is an optional string, defaulting to an empty
  string.
- `intro_message: Optional[str] = ""` - The introduction message of the bot. This is an optional string. If this is an
  empty string, then the bot will not have an introduction message.
- `prompt_public: Optional[bool] = True` - Whether the preset personality should be publicly visible. This is an
  optional boolean, defaulting to True.
- `profile_picture_url: Optional[str] = None` - The URL of the bot's profile picture. This is an optional string,
  defaulting to `None`. Using this library, you cannot actually upload custom images.
- `linkification: Optional[bool] = False` - Whether the bot should convert some text in responses into clickable links.
  This is an optional boolean, defaulting to False.
- `markdown_rendering: Optional[bool] = True` - Whether the bot's responses enable markdown rendering. This is an
  optional boolean, defaulting to True.
- `suggested_replies: Optional[bool] = False` - Whether the bot should suggest possible replies after each response.
  This is an optional boolean, defaulting to False.
- `private: Optional[bool] = False` - Whether the bot should be private. This is an optional boolean, defaulting to
  False.
- `temperature: Optional[float] = None` - The temperature of the bot. This is an optional floating-point number,
  defaulting to `None`.

If you want the new bot to use your own API (the official Poe access tutorial can be
found [here ↗](https://github.com/poe-platform/api-bot-tutorial)), please use the following parameters:

- `api_bot = False` - Whether the bot is your own API bot.
- `api_key = None` - The API key for the new bot.
- `api_url = None` - The API URL for the new bot.

```python
await poe_client.edit_bot(url_botname="test27gs", handle="test27gs2", prompt="a computer programmer")
```

---

### 4. Delete a bot

Note, this operation is irreversible!

Function: `delete_bot()`

Parameters:

- `url_botname: str` - The url_name of the bot.

Return value: `None`

```python
await poe_client.delete_bot(url_botname="test27gs2")
```

---

### 5. Chat with a Bot

#### (1). Using websockets and httpx support for streaming output and suggested replies

Function: `ask_stream()`

Parameters:

- `url_botname: str` - The url_name of the bot.
- `question: str` - The content of the query.
- `suggest_able: Optional[bool]` - Whether to display suggested responses (the bot must support suggested responses to
  output them together).
- `with_chat_break: Optional[bool]` - Whether to clear the bot's memory after the dialogue (i.e., maintain a single
  dialogue).

Return value: `AsyncGenerator` of `str`

```python
# The usage of get_available_bots() can be seen in section 8.
bots = await poe_client.get_available_bots(count=2)
async for message in poe_client.ask_stream(url_botname=bots[1]['handle'], question="introduce websockets"):
    print(message, end="")
# If suggested replies are used and a list of suggested replies is desired, you can extract from the bots property.
# It records the latest suggested replies of a bot.
print(poe_client.bots[bots[1]['handle']]['Suggestion'])
```

#### (2). Function that only uses httpx and does not support suggested replies and streaming output

Function: `ask()`

Parameters:

- `url_botname: str` - The url_name of the bot.
- `question: str` - The content of the query.
- `with_chat_break: Optional[bool]` - Whether to clear the bot's memory after the dialogue (i.e., maintain a single
  dialogue).

Return value: `str`

```python
answer = await poe_client.ask(url_botname="Assistant", question="Introduce openai")
print(answer)
```

---

### 6. Deleting a bot's dialogue memory, resetting the dialogue (This does not delete messages in the chat history)

Function: `send_chat_break()`

Parameters:

- `url_botname: str` - The url_name of the bot whose memory you want to clear.

Return value: `None`

```python
await poe_client.send_chat_break(url_botname="Assistant")
```

---

### 7. Get your own available bots

Note that the query order is from top to bottom according to the order of the left sidebar on poe.com.  
Function: `get_available_bots()`

Parameters:

- `count: Optional[str] = 25` - The number of bots to get.
- `get_all: Optional[bool] = False` - Whether to directly get all bots.

Return value: `List[dict]` - A list containing dictionaries of bot information. In this list, whether it's a system bot
or a bot you created, their handle is always equal to url_botname.

```python
poe_client = await Poe_Client("your p_b token").create()
bots = await poe_client.get_available_bots(count=2)
print(bots)
bots = await poe_client.get_available_bots(get_all=True)
print(bots)
```

---

### 8. Bulk Delete your Available Bots

Please note that the deletion order is from top to bottom according to the order of the left sidebar on poe.com, and if
you encounter a system-supplied bot, it will be skipped directly but will also be counted in the quantity.

Warning: This operation is irreversible!
Function: `delete_available_bots()`

Parameters:

- `count: Optional[int] = 2` - The number of bots to be deleted (note this cannot delete system bots, so the actual
  number deleted may not match this count).
- `del_all: Optional[bool] = False` - Whether to directly delete all bots (note that deleting all bots may take a long
  time, depending on the number of bots you have).

Return value: `None`

```python
await poe_client.delete_available_bots(count=2)
await poe_client.delete_available_bots(del_all=True)
```

---

### 9. Get partial data or full settings of a bot

Function: `get_botdata()`

Parameters:

- `url_botname: str` - The url_name of the bot whose memory you want to clear.

Return value:  
A dictionary containing some of the bot's chat history and information.

```python
data = await poe_client.get_botdata(url_botname="578feb1716fe43f")
print(data)
```

Function: `get_bot_info()`

Parameters:

- `url_botname: str` - The url_name of the bot whose memory you want to clear.

Return value:  
A dictionary containing all the information of the bot, such as the parameters when creating or editing the bot, for
example, prompt and personality preset.

```python
info = await poe_client.get_bot_info(url_botname="578feb1716fe43f")
print(info)
```

---

### 10. Get Chat History (Chat Messages)

Please note that the retrieval order is from most recent to oldest, but the output is first the older ones, then the
newer ones, which is exactly the same as your operation on the webpage by scrolling up.

Function: `get_message_history()`

Parameters:

- `url_botname: str` - The url_name of the bot for which you want to retrieve chat messages.
- `count: Optional[int] = 2` - The number of messages to retrieve.
- `get_all: Optional[bool] = False` - Whether to directly retrieve all chat messages with this bot.

Return value: `List[dict]` - A list containing dictionaries of chat messages.

```python
messages = await poe_client.get_message_history(url_botname="GPT-4", count=20)
print(messages)
messages = await poe_client.get_message_history(url_botname="GPT-4", get_all=True)
print(messages)
```

---

### 11. Delete Chat History (Chat Messages)

Warning: This operation is irreversible!

#### (1). Delete Chat History with a Certain Bot

Function: `delete_bot_conversation`

Parameters:

- `url_botname: str` - The url_name of the bot for which you want to delete chat messages.
- `count: Optional[int] = 2` - The number of messages to delete.
- `del_all: Optional[bool] = False` - Whether to directly delete all chat messages with this bot.

Return value: `None`

```python
await poe_client.delete_bot_conversation(url_botname="Assistant", count=2)
await poe_client.delete_bot_conversation(url_botname="Assistant", del_all=True)
```

#### (2). Delete All Chat History with All Bots

Function: `delete_all_conversations()`  
No parameters  
Return value: `None`

```python
await poe_client.delete_all_conversations()
```

---

### 12. Get Bots Created by Others (Bots in [explore](https://poe.com/explore_bots?category=All) page)

Please note that the retrieval order is from top to bottom, in accordance with the order on poe.com.

Function: `explore_bots()`

Parameters:

- `count: Optional[str] = 25` - The number of bots to retrieve.
- `get_all: Optional[bool] = False` - Whether to directly retrieve all bots.

Return value: `List[dict]` - A list containing dictionaries of bot information. In this list, whether it's a system bot
or a bot you created, their handle is always equal to url_botname.

```python
bots = await poe_client.explore_bots(count=100)
print(bots)
bots = await poe_client.explore_bots(get_all=True)
print(bots)
```
