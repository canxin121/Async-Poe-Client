# 使用指南

这是如何使用`Poe_Client`库的指南。在开始之前，请确保你已经安装了这个库。

QA:

- 一.url_botname是什么? -> 在使用poe的某个bot时,链接中的bot的名称("https://poe.com/ChatGPT" 中是 'ChatGPT').  
  这个url_botname和其他name的关系可以理解为:  
  1.对于系统的自带的bot,你在poe网页上看到的bot的名称和url_name永远相等(
  但是都不等于handle)  
  2.对于自己创建的bot,url_name =
  handle,如果设置了display_name,那么在网页上看到的名字是display_name,如果没设置,看到的就是url_name(handle)  
  但是有特殊的情况下handle并不遵循上面的规律,比如使用get_available_bots得到的所有bot的handle都永远等于url_botname

## 步骤1：导入库并创建Poe_Client对象

在使用`Poe_Client`库的任何功能之前，需要首先导入库并创建一个`Poe_Client`对象。需要传递`p_b token`给`Poe_Client`
的构造函数，然后调用`create`方法来初始化它。下面是一个示例：

```python
from async_poe_client import Poe_Client

poe_client = await Poe_Client("your p_b token").create()
```

其中，`"your p_b token"`应该被替换为你的p_b token。

## 步骤2：使用Poe_Client

在创建了`Poe_Client`后，你就可以使用它进行非常多的操作.
---

### 1.获取账号的订阅信息

直接获取属性值即可,其值是一个包含订阅信息的dict

```python
print(poe_client.subscription)
```

---

### 2.获取账号上所有的可以使用的bot的信息

注意获取的顺序是从上到下,按照poe.com首页的顺序获取的,既能获取系统自带的bot,也可以获取自己创建的bot

函数:get_available_bots()

参数:

- ` count: Optional[int] = 2` - 要获取的bot的数量
- `get_all: Optional[bool] = False` - 是否直接获取所有的自己的聊天消息

返回值: List[dict]  
这里每个dict中的 handle 永远等于 在其他功能中可以使用的url_name

获取指定数量的bot

```python
bots = await poe_client.get_available_bots(count=25)
print(bots)
```

获取所有的bot

```python
bots = await poe_client.get_available_bots(get_all=True)
print(bots)
```

---

### 3.创建一个bot

函数:create_bot()

参数:

- `handle: str` - 新 bot 的名称，必须是字符串类型,而且这个名字在整个poe.com中都必须是唯一的,和别人的重名也不行。
- `prompt: str = ""` - 新 bot 的预设人格，可选字符串类型，默认为空字符串。
- `display_name: Optional[str] = `None`` - 新 bot 的显示名称，可选字符串类型，默认为`None`。如果不传递，将显示handle。
- `base_model: str = "chinchilla"` - 新 bot 使用的模型，可选字符串类型。选项包括："chinchilla" (ChatGPT) 或 "a2" (Claude)
  。如果已经订阅，可以使用 "beaver" (ChatGPT4) 或 "a2_2" (Claude-2-100k)。
- `description: str = ""` - 新 bot 的描述，可选字符串类型，默认为空字符串。
- `intro_message: str = ""` - 新 bot 的介绍信息，可选字符串类型。如果这是一个空字符串，则 bot 将没有介绍信息。
- `prompt_public: bool = True` - 预设人格是否应公开可见，可选布尔类型，默认为True。
- `profile_picture_url: Optional[str] = `None`` - bot 的个人资料图片的 URL，可选字符串类型，默认为`None`
  。使用这个库实际上无法上传自定义图像。
- `linkification: bool = False` - bot 是否应将响应中的某些文本转化为可点击的链接，可选布尔类型，默认为False。
- `markdown_rendering: bool = True` - bot 的响应是否启用 markdown 渲染，可选布尔类型，默认为True。
- `suggested_replies: bool = False` - bot 是否应在每次响应后建议可能的回复，可选布尔类型，默认为False。
- `private: bool = False` - bot 是否应为私人的，可选布尔类型，默认为False。
- `temperature: Optional[float] = `None`` - 新 bot 的温度，可选浮点数类型，默认为`None`。

如果你希望新的 bot 使用你自己的 API（在[这里](https://github.com/poe-platform/api-bot-tutorial)可以获取poe官方的接入教程），请使用以下参数：

- `api_bot = False` - bot 是否是 自己的API bot。
- `api_key = `None`` - 新 bot 的 API 密钥。
- `api_url = `None`` - 新 bot 的 API URL。
  返回值:`None`

最简单的用例如下,只需要传递hanlde和prompt就可以创建一个bot

```python
await poe_client.create_bot(handle="testbotcx1", prompt="a ai assistant", p)
```

---

### 3.修改一个bot的设置

函数:edit_bot()

参数:  
注意下面只有url_botname是bot原来的名字,其他的都是要修改成的参数,如果不传递,则这个参数会保持不变

- `url_botname: str` - 所要修改的bot的url_name，必须是字符串类型。
- `handle: Optional[str]` - bot 的名称，必须是字符串类型，且在整个poe.com中必须是唯一的，不能与其他bot重名。
- `prompt: Optional[str] = ""` - bot 的预设人格，可选字符串类型，默认为空字符串。
- `display_name: Optional[str] = `None`` - bot 的显示名称，可选字符串类型，默认为`None`。如果不传递，将显示handle。
- `base_model: Optional[str] = "chinchilla"` - bot 使用的模型，可选字符串类型。选项包括："chinchilla" (ChatGPT) 或 "a2" (
  Claude)。如果已经订阅，可以使用 "beaver" (ChatGPT4) 或 "a2_2" (Claude-2-100k)。
- `description: Optional[str] = ""` - bot 的描述，可选字符串类型，默认为空字符串。
- `intro_message: Optional[str] = ""` - bot 的介绍信息，可选字符串类型。如果这是一个空字符串，则 bot 将没有介绍信息。
- `prompt_public: Optional[bool] = True` - 预设人格是否应公开可见，可选布尔类型，默认为True。
- `profile_picture_url: Optional[str] = `None`` - bot 的个人资料图片的 URL，可选字符串类型，默认为`None`
  。使用这个库实际上无法上传自定义图像。
- `linkification: Optional[bool] = False` - bot 是否应将响应中的某些文本转化为可点击的链接，可选布尔类型，默认为False。
- `markdown_rendering: Optional[bool] = True` - bot 的响应是否启用 markdown 渲染，可选布尔类型，默认为True。
- `suggested_replies: Optional[bool] = False` - bot 是否应在每次响应后建议可能的回复，可选布尔类型，默认为False。
- `private: Optional[bool] = False` - bot 是否应为私人的，可选布尔类型，默认为False。
- `temperature: Optional[float] = `None`` - bot 的温度，可选浮点数类型，默认为`None`。

如果你希望新的 bot 使用你自己的 API（在[这里](https://github.com/poe-platform/api-bot-tutorial)可以获取poe官方的接入教程），请使用以下参数：

- `api_bot = False` - bot 是否是 自己的API bot。
- `api_key = `None`` - 新 bot 的 API 密钥。
- `api_url = `None`` - 新 bot 的 API URL。

```python
await poe_client.edit_bot(url_botname="test27gs", handle="test27gs2", prompt="a computer programmer")
```

---

### 3.删除一个bot

注意,这个操作是不可逆的!

函数:delete_bot()

参数:

- `url_botname:str` - bot的url名

返回值:`None`

```python
await poe_client.delete_bot(url_botname="test27gs2")
```

---
### 4.和bot对话
---

#### (1).使用websockets和httpx的支持流式输出和建议回复的函数

函数:ask_stream()
参数:

- `url_botname:str` - bot的url名
- `question:str` - 询问的内容
- `suggest_able:Optional[bool]` - 是否显示建议回复(需要该bot支持建议回复才能一并输出出来)
- `with_chatb_reak:Optional[bool]` - 是否在对话后清除bot的记忆(即保持单对话)

返回值:str的AsyncGenerator

```python
bots = await poe_client.get_available_bots(count=2)
async for message in poe_client.ask_stream(url_botname=bots[0]['handle'], question="introduce websockets"):
    print(message, end="")
```

---

#### (2).仅使用httpx的不支持建议回复和流式输出的函数

函数:ask()

参数:

- `url_botname:str` - bot的url名
- `question:str` - 询问的内容
- `with_chatb_reak:Optional[bool]` - 是否在对话后清除bot的记忆(即保持单对话)

返回值:str

```python
answer = await poe_client.ask(url_botname="Assistant", question="Introduce openai")
print(answer)
```

---

### 7.删除bot的对话记忆,重置对话(这并不会删除聊天记录中的消息)

函数:send_chat_break()

参数:

- `url_botname:str` - 要清除记忆的bot的url_botname

返回值:`None`

```python
await poe_client.send_chat_break(url_botname="Assistant")
```

---

### 6.查询自己的可用的bot

注意查询的顺序是按照poe.com左侧边栏的顺序从上往下查询的  
函数:get_available_bots()

参数:

- `count:Optional[str]=25` - 要获取的bot的数量
- `get_all:Optional[bool]=False` - 是否直接获取所有的bot

返回值:`List[dict]` - 包含bot信息dict的list,这个list中的无论系统bot还是自己创建的bot,其handle都永远等于url_botname

```python
poe_client = await Poe_Client("your p_b token").create()
bots = await poe_client.get_available_bots(count=2)
print(bots)
bots = await poe_client.get_available_bots(get_all=True)
print(bots)
```

---

### 7.批量删除自己可用的bot

注意删除顺序是按照poe.com左侧边栏的顺序从上往下查询的,并且如果碰到系统自带的bot,会直接跳过,但是也计算在数量之中了

注意: 这个操作是不可逆的!
函数:delete_available_bots()

参数:

- ` count: Optional[int] = 2` - 要删除的bot的数量(注意这并不能删除系统的bot,所以该数量和实际删除的数量并不相等)
- `del_all: Optional[bool] = False` - 是否直接删除所有的bot(注意删除所有bot的时间可能很长,这取决于你的bot的数量)

返回值:`None`

```python
await poe_client.delete_available_bots(count=2)
await poe_client.delete_available_bots(del_all=True)
```

---

### 7.获取bot的部分数据或设置信息

函数: get_botdata()

参数:

- `url_botname:str` - 要清除记忆的bot的url_botname

返回值:  
一个包含bot的部分聊天记录和部分信息的dict

```python
data = await poe_client.get_botdata(url_botname="578feb1716fe43f")
print(data)
```

函数:get_bot_info()

参数:

- `url_botname:str` - 要清除记忆的bot的url_botname

返回值:  
一个包含bot的所有的信息的dict,这些信息就是在创建bot或者编辑bot时的那些参数,比如prompt 人格预设

```python
info = await poe_client.get_bot_info(url_botname="578feb1716fe43f")
print(info)
```

---

### 8.获取聊天记录(聊天消息)

注意获取的顺序是由最近到之前,但是输出时是先输出先前的,在输出现在的,也就是和你在网页上向上滑动的操作完全相同

函数:get_message_history()

参数:

- `url_botname:str` - 要获取聊天消息的bot的url_botname
- ` count: Optional[int] = 2` - 要或缺的消息的数量
- `del_all: Optional[bool] = False` - 是否直接或取所有的和该bot的聊天消息

返回值:`List[dict]` - 包含聊天消息dict的列表

```python
messages = await poe_client.get_message_history(url_botname="GPT-4", count=20)
print(messages)
messages = await poe_client.get_message_history(url_botname="GPT-4", get_all=True)
print(messages)
```

---

### 9.删除聊天记录(聊天消息)

注意: 这个操作是不可逆的!
---

#### (1). 删除和某个bot的聊天记录

函数:delete_bot_conversation

参数:

- `url_botname:str` - 要删除聊天记录的bot的url_botname
- ` count: Optional[int] = 2` - 要删除的消息的数量
- `del_all: Optional[bool] = False` - 是否直接删除所有的和该bot的聊天消息

返回值:`None`

```python
await poe_client.delete_bot_conversation(url_botname="Assistant", count=2)
await poe_client.delete_bot_conversation(url_botname="Assistant", del_all=True)
```

---

#### (2). 删除和所有bot的所有聊天记录

函数:delete_all_conversations()  
无参数  
返回值:`None`

```python
await poe_client.delete_all_conversations()
```

---

### 10.获取其他人创建的bot(poe.com左上角explor中的bot)

注意获取的顺序是从上到下,按照poe.com首页的顺序获取的,既能获取系统自带的bot,也可以获取自己创建的bot

函数:explore_bots()

参数:

- `count:Optional[str]=25` - 要获取的bot的数量
- `get_all:Optional[bool]=False` - 是否直接获取所有的bot

返回值:`List[dict]` - 包含bot信息dict的list,这个list中的无论系统bot还是自己创建的bot,其handle都永远等于url_botname

```python
bots = await poe_client.explore_bots(count=100)
print(bots)
bots = await poe_client.explore_bots(explore_all=True)
print(bots)
```
