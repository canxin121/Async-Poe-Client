# User Guide

[中文说明](README_zh_CN.md)

Maintenance has been discontinued due to too harsh restrictions on free users.  
Maintenance has been discontinued due to too harsh restrictions on free users.  
Maintenance has been discontinued due to too harsh restrictions on free users.  
![image](https://github.com/canxin121/Async-Poe-Client/assets/69547456/f4adb7a3-7ad5-4c3b-8596-769e5716b350)


Latest Version: 0.2.9
This is a guide on how to use the `async-poe-Client` library. Before getting started, make sure you have installed this
library.

```
pip install async-poe-client
```

## Table of Contents

- [QA](#qa)
- [Step 1: Import Libraries and Create Poe_Client Object](#step-1-import-the-library-and-create-a-poeclient-object)
- [Step 2: Using Poe_Client](#step-2-using-poeclient)
    - [1. Get Subscription Information](#1-get-subscription-information-for-an-account)
    - [2. Create a Bot](#2-create-a-bot)
    - [3. Modify Bot Settings](#3-modify-the-settings-of-a-bot)
    - [4. Delete a Bot](#4-delete-a-bot)
    - [5. Chat with a Bot](#5-chat-with-a-bot)
    - [6. Clear Bot's Conversation Memory and Reset Dialogue (Does Not Delete Chat Messages)](#6-reset-the-conversation-memory-of-a-bot-without-deleting-chat-history)
    - [7. Retrieve User's Available Bots](#7-get-available-bots)
    - [8. Batch Delete User's Available Bots](#8-batch-delete-available-bots)
    - [9. Get Bot Data or Settings Information](#9-get-bot-data-or-settings-information)
    - [10. Delete Chat Windows with a Bot](#10-delete-chat-windows-with-a-bot)
    - [11. Get Bots Created by Others (From "Explore" Section on poe.com)](#11-get-bots-created-by-others-from-the-explore-section-on-poecom)
    - [12. Get Bot chat history](#12-get-bot-chat-history-messages)

# QA:

- Question: What is url_botname? -> When using a specific bot in Poe, the bot's name in the
  URL ("https://poe.com/ChatGPT" where 'ChatGPT' is the url_botname) is referred to as url_botname. The relationship
  between url_botname and other names can be understood as follows:

    1. For built-in system bots, the bot's name you see on the Poe website will always be equal to url_botname (but not
       equal to handle).
    1. For self-created bots, url_botname = handle. If a display_name is set, the name you see on the website will be
       the display_name. Otherwise, it will be the url_botname (handle). However, there are some special cases where the
       handle does not follow the above pattern, such as when using get_available_bots, where all bot handles are always
       equal to url_botname.

- Question: What is chat_code? ->
  A bot can have multiple chat windows, and chat_code is the unique identifier for each chat window. The method to
  retrieve it is similar to url_botname. For example, in "https://poe.com/chat/1234567890", the chat_code is 1234567890.

- Question: How to obtain p_b and formkey? ->

    1. Obtaining p_b: Open poe.com, use F12 to open the debugging tools, and navigate to the Application tab. In the
       cookies, there will be a value for p_b.
    1. Obtaining formkey: Open poe.com, use F12 to open the debugging tools, and navigate to the Network tab. After
       having a conversation with a bot, you can see the gql_POST network request, where the request headers contain a
       separate formkey key-value pair.

## Step 1: Import the library and create a Poe_Client object

Now the formkey must be filled in to use the library. Currently, no solution has been found for the "document is not
defined" error.
~~If you do not pass the formkey, you need to install Node.js to use the formkey generation feature. Here is the
download link: [node.js](https://nodejs.org/en)~~

Before using any functionality of the `Poe_Client` library, you need to import the library and create a `Poe_Client`
object. You need to pass the `p_b token` and `formkey` to the constructor of `Poe_Client`, and then call the `create`
method to initialize it. Here is an example:

```python
from async_poe_client import Poe_Client

# If the creation process takes a long time, you can try setting preload to False
poe_client = await Poe_Client("your p_b token", "your form key").create()
# You can also set a proxy
poe_client = await Poe_Client("your p_b token", "your form key", proxy="socks5://127.0.0.1:7890").create()
```

In the above code, `"your p_b token"` and `"your form key"` should be replaced with your actual p_b token and formkey.

## Step 2: Using Poe_Client

Once you have created `Poe_Client`, you can perform various operations with it.

______________________________________________________________________

### 1. Get subscription information for an account

You can directly access the attribute value.

```python
print(poe_client.subscription)
```

It returns a dictionary containing the subscription information.

______________________________________________________________________

### 2. Create a bot

Function: `create_bot()`

Parameters:

- `handle: str` - The name of the new bot. It must be a string and must be unique throughout poe.com. It cannot have the
  same name as another bot.
- `prompt: str = ""` - The preset personality of the new bot. It is an optional string parameter and defaults to an
  empty string.
- `display_name: Optional[str] = `None\`\` - The display name of the new bot. It is an optional string parameter and
  defaults to `None`. If not passed, the handle will be displayed.
- `base_model: str = "chinchilla"` - The model used by the new bot. It is an optional string parameter. The options
  are: "chinchilla" (ChatGPT) or "a2" (Claude). If subscribed, you can use "beaver" (ChatGPT4) or "a2_2" (
  Claude-2-100k).
- `description: str = ""` - The description of the new bot. It is an optional string parameter and defaults to an empty
  string.
- `intro_message: str = ""` - The introduction message of the new bot. It is an optional string parameter. If it is an
  empty string, the bot will have no introduction message.
- `prompt_public: bool = True` - Whether the preset personality should be publicly visible. It is an optional boolean
  parameter and defaults to True.
- `profile_picture_url: Optional[str] = `None\`\` - The URL of the profile picture for the bot. It is an optional string
  parameter and defaults to `None`. The library does not support uploading custom images.
- `linkification: bool = False` - Whether the bot should convert certain text in responses into clickable links. It is
  an optional boolean parameter and defaults to False.
- `markdown_rendering: bool = True` - Whether the bot's responses should enable markdown rendering. It is an optional
  boolean parameter and defaults to True.
- `suggested_replies: bool = True` - Whether the bot should suggest possible replies after each response. It is an
  optional boolean parameter and defaults to False.
- `private: bool = False` - Whether the bot should be private. It is an optional boolean parameter and defaults to
  False.
- `temperature: Optional[float] = `None\`\` - The temperature of the new bot. It is an optional float parameter and
  defaults to `None`.

If you want the new bot to use your own API (you can find the official Poe API integration
tutorial [here](https://github.com/poe-platform/api-bot-tutorial)), use the following parameters:

- `api_bot = False` - Whether the bot is your own API bot.
- `api_key = `None\`\` - The API key for the new bot.
- `api_url = `None\`\` - The API URL for the new bot.

Return value: `None`

The simplest usage is as follows, where you only need to pass the handle and prompt to create a bot:

```python
await poe_client.create_bot(handle="testbotcx1", prompt="a ai assistant", p)
```

______________________________________________________________________

### 3. Modify the settings of a bot

Function: `edit_bot()`

Parameters:\
Note that `url_botname` is the original name of the bot, and the other parameters are the values to be modified. If a
parameter is not passed, its value will remain unchanged.

- `url_botname: str` - The `url_botname` of the bot to be modified, must be a string.
- `handle: Optional[str]` - The name of the bot, must be a string and must be unique across the entire poe.com. It
  cannot be the same as any other bot.
- `prompt: Optional[str] = ""` - The preset personality of the bot, optional string, defaults to an empty string.
- `display_name: Optional[str] = `None\`\` - The display name of the bot, optional string, defaults to `None`. If not
  passed, the handle will be displayed.
- `base_model: Optional[str] = "chinchilla"` - The model used by the bot, optional string. Options include: "
  chinchilla" (ChatGPT) or "a2" (Claude). If subscribed, you can use "beaver" (ChatGPT4) or "a2_2" (Claude-2-100k).
- `description: Optional[str] = ""` - The description of the bot, optional string, defaults to an empty string.
- `intro_message: Optional[str] = ""` - The introduction message of the bot, optional string. If it is an empty string,
  the bot will have no introduction message.
- `prompt_public: Optional[bool] = True` - Whether the preset personality should be publicly visible, optional boolean,
  defaults to True.
- `profile_picture_url: Optional[str] = `None\`\` - The URL of the profile picture of the bot, optional string, defaults
  to `None`. With this library, it is not possible to upload custom images.
- `linkification: Optional[bool] = False` - Whether the bot should convert certain text in the response into clickable
  links, optional boolean, defaults to False.
- `markdown_rendering: Optional[bool] = True` - Whether the bot's response should enable markdown rendering, optional
  boolean, defaults to True.
- `suggested_replies: Optional[bool] = False` - Whether the bot should suggest possible replies after each response,
  optional boolean, defaults to False.
- `private: Optional[bool] = False` - Whether the bot should be private, optional boolean, defaults to False.
- `temperature: Optional[float] = `None\`\` - The temperature of the bot, optional float, defaults to `None`.

If you want the new bot to use your own API (you can get the official Poe API integration
tutorial [here](https://github.com/poe-platform/api-bot-tutorial)), use the following parameters:

- `api_bot = False` - Whether the bot is your own API bot.
- `api_key = `None\`\` - The API key for the new bot.
- `api_url = `None\`\` - The API URL for the new bot.

```python
await poe_client.edit_bot(url_botname="test27gs", handle="test27gs2", prompt="a computer programmer")
```

______________________________________________________________________

### 4. Delete a bot

Note: This operation is irreversible!

Function: `delete_bot()`

Parameters:

- `url_botname: str` - The URL name of the bot.

Returns: `None`

```python
await poe_client.delete_bot(url_botname="test27gs2")
```

______________________________________________________________________

### 5. Chat with a bot

(1). Function that returns pure text format:

Function: ask_stream()
Parameters:

- `url_botname: str` - The URL name of the bot.
- `chat_code: Optional[str]` - The unique identifier for a specific chat window of the bot.
- `question: str` - The content of the inquiry.
- `suggest_able: Optional[bool]` - Whether to display suggested replies (requires bot support for suggested replies to
  be output).
- `with_chatb_reak: Optional[bool]` - Whether to clear the bot's memory after the conversation (i.e., maintain a single
  dialogue).

Return value: AsyncGenerator of str

```python
# The get_available_bots() function can be found in item 8 with usage instructions.
# If chat_code is not provided, a new chat window will be automatically created, and its chat_code can be obtained from the poe_client's property.
async for message in poe_client.ask_stream(url_botname='ChatGPT', question="introduce async and await"):
    print(message, end="")

# The bot_code_dict attribute can be accessed to get a dictionary with url_botname as the key and List[chat_code] as the value. The order is from newest to oldest, and the first one is the chat_code that was just automatically created.
chat_code = poe_client.bot_code_dict['ChatGPT'][0]

# Continue the conversation using the chat_code obtained earlier
async for message in poe_client.ask_stream(url_botname='ChatGPT', chat_code=chat_code,
                                           question="introduce async and await"):
    print(message, end="")

# If suggested replies are used and you want a list of suggested replies, they can be extracted from the bots attribute, which records the last suggested reply of a bot in a specific chat.
print(poe_client.bots['ChatGPT']['chats'][chat_code]['Suggestion'])
```

(2). Function that returns corresponding information format:

Function: ask_stream_raw()
Parameters:

- `url_botname: str` - The URL name of the bot.
- `chat_code: Optional[str]` - The unique identifier for a specific chat window of the bot.
- `question: str` - The content of the inquiry.
- `suggest_able: Optional[bool]` - Whether to display suggested replies (requires bot support for suggested replies to
  be output).
- `with_chatb_reak: Optional[bool]` - Whether to clear the bot's memory after the conversation (i.e., maintain a single
  dialogue).

Return value: AsyncGenerator of Text, SuggestRely, ChatCodeUpdate, ChatTiTleUpdate

```python
from async_poe_client import Text, SuggestRely, ChatTiTleUpdate, ChatCodeUpdate

suggest_replys = []
chat_title = None
async for data in poe_client.ask_stream_raw(url_botname="ChatGPT", question="介绍一下微软",
                                        suggest_able=True):

    # You can use the content attribute to get the specific content of the corresponding type, or use str() directly.
    if isinstance(data, Text):
        """Text response"""
        print(str(data), end="")
    elif isinstance(data, SuggestRely):
        """Suggested reply"""
        suggest_replys.append(str(data))
        if len(suggest_replys) == 1:
            print("\nSuggest Replys:\n")
        print(f"{len(suggest_replys)}: {data}")
    elif isinstance(data, ChatTiTleUpdate):
        """Chat window title update"""
        chat_title = data
    elif isinstance(data, ChatCodeUpdate):
        """New chat_code"""
        print("\nNew ChatCode: " + str(data))

if chat_title:
    print(f"\nNew Chat Title: {chat_title}")
```

### 6. Reset the conversation memory of a bot (without deleting chat history)

Function: `send_chat_break()`

Parameters:

- `url_botname: str` - The URL name of the bot whose memory is to be cleared.
- `chat_code: str` - The unique identifier of the conversation to be cleared.

Returns: `None`

```python
await poe_client.send_chat_break(url_botname="Assistant", chat_code="chat_code")
```

______________________________________________________________________

### 7. Get available bots

Note that the order of retrieval is based on the order in the left sidebar of poe.com, from top to bottom.

Function: `get_available_bots()`

Parameters:

- `count: Optional[str] = 25` - The number of bots to retrieve.
- `get_all: Optional[bool] = False` - Whether to retrieve all available bots.

Returns: `List[dict]` - A list containing dictionaries of bot information. The `handle` of both system bots and
user-created bots will always be the same as the `url_botname`.

```python
# By default, when creating the client, the information of all bots is automatically loaded and stored in the `bots` attribute. The process of creating and deleting bots (excluding automatically added sent and received messages in chat windows) will also be reflected in the `bots` attribute of the client.
poe_client = await Poe_Client("your p_b token", "formkey").create()
print(poe_client.bots)

# You can also actively retrieve available bots
bots = await poe_client.get_available_bots(get_all=True)
print(bots)
```

______________________________________________________________________

### 8. Batch delete available bots

Note that the deletion order is based on the order in the left sidebar of poe.com, and if a system bot is encountered,
it will be skipped. However, it is counted in the quantity.

Note: This operation is irreversible!

Function: `delete_available_bots()`

Parameters:

- `count: Optional[int] = 2` - The number of bots to delete (Note that this does not include system bots, so the actual
  number of deletions may be different).
- `del_all: Optional[bool] = False` - Whether to delete all available bots (Note that deleting all bots may take a long
  time depending on the number of bots you have).

Returns: `None`

```python
await poe_client.delete_available_bots(count=2)
await poe_client.delete_available_bots(del_all=True)
```

---

### 9. Get bot data or settings information

Function: `get_botdata()`

Parameters:

- `url_botname: str` - The URL name of the bot.

Returns:
A dictionary containing some chat messages and partial information of the bot.

```python
data = await poe_client.get_botdata(url_botname="578feb1716fe43f")
print(data)
```

Function: `get_bot_info()`

Parameters:

- `url_botname: str` - The URL name of the bot.

Returns:\
A dictionary containing all information of the bot, such as prompt and persona, which are the parameters used when
creating or editing the bot.

```python
info = await poe_client.get_bot_info(url_botname="578feb1716fe43f")
print(info)
```

______________________________________________________________________

### 10. Delete chat windows with a bot

Note: This operation is irreversible!

#### (1) Delete a specific chat window with a bot

Function: `delete_chat_by_chat_code()`

Parameters:

- `chat_code: str` - The chat code of the conversation window to delete.

Returns: `None`

```python
await poe_client.delete_chat_by_chat_code(chat_code="chat_code")
```

#### (2) Delete a specified number of chat windows with a bot

Function: `delete_chat_by_count()`

- `url_botname: str`
- `count: int` - The number of chat windows to delete (from top to bottom).
- `del_all: bool` - Whether to delete all chat windows.

Returns: `None`

```python
# Delete 20 chat windows
await poe_client.delete_chat_by_count(url_botname="ChatGPT", count=20)
# Delete all chat windows
await poe_client.delete_chat_by_count(url_botname="ChatGPT", del_all=True)
```

______________________________________________________________________

### 11. Get bots created by others (from the "Explore" section on poe.com)

Note that the retrieval order is from top to bottom, based on the order on poe.com.

Function: `explore_bots()`

Parameters:

- `count: Optional[str] = 25` - The number of bots to retrieve.
- `get_all: Optional[bool] = False` - Whether to retrieve all available bots.

Returns: `List[dict]` - A list containing dictionaries of bot information. The `handle` of both system bots and
user-created bots will always be the same as the `url_botname`.

```python
bots = await poe_client.explore_bots(count=100)
print(bots)
bots = await poe_client.explore_bots(explore_all=True)
print(bots)
```

### 12. Get bot chat history (messages)

Function: `get_chat_history()`

Parameters:

- `url_botname: str` - The URL name of the bot.
- `chat_code: str` - The chat to get
- `count: int = 25` - The count of messages to get
- `get_all: bool = False` - Whether to get all the chat messages
  Returns:
  A list of dictionary containing some chat messages of the chat.

```python
history = await poe_client.get_chat_history("ChatGPT", "chat_code", get_all=True)
print(history)
```
