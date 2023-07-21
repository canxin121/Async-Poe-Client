# Async-Poe-Client
todo  
- explore third_party bots
- delete bot

```python
import asyncio

from Async_Poe_Client import Async_Poe_Client

"""
This is a temp example

In this module, the url name means the bot name in the url when using a bot
example: when using https://poe.com/Assistant, the 'url_botnam' is Assistant
"""


async def main():
    """create an instance of Async_Poe_Client"""
    poe_client = await Async_Poe_Client("your token here").create()
    """ask a question and get answer with and http websockets which could stream output and has suggestions"""
    async for message in poe_client.ask_stream(url_botname="Assistant", question="hello,who are you?",
                                               suggest_able=True):
        print(message, end="")
    """ask a question and get answer with onlt http(no suggestions)"""
    answer = await poe_client.ask(url_botname="Assistant", question="Introduce openai", plain=True)
    
    """send chat break(claer the bot's memory)"""
    await poe_client.send_chat_break(url_botname="Assistant")
    
    """create a bot"""
    await poe_client.create_bot(handle="canxintest01", prompt="a ai assistant")
    
    """edit a bot"""
    await poe_client.edit_bot(url_botname="canxintest01", prompt="a computer programmer")
    
    """delete some conservation messages with specific bot"""
    await poe_client.delete_bot_conversation(url_botname="Assistant", count=2)
    
    """delete all conservation messages with specific bot"""
    await poe_client.delete_bot_conversation(url_botname="Assistant", del_all=True)
    
    """delete all conservation messages with all bots"""
    await poe_client.delete_all_conversations()
    
    """get some conversation messages with specific bot"""
    messages = await poe_client.get_message_history(url_botname="Assistant",count=20)
    
    """get all conversation messages with specific bot"""
    messages = await poe_client.get_message_history(url_botname="Assistant",count=20)
    
    """get bot configuration"""
    config = await poe_client.get_bot_configuration(url_botname="canxintest01")

```
