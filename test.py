import random
import string

import pytest

from async_poe_client import Poe_Client


def generate_random_str(length, charset=string.ascii_lowercase + string.digits):
    random_str = ''.join(random.choice(charset) for i in range(length))
    return random_str


@pytest.mark.asyncio
async def test_get_subscription_info():
    poe_client = await Poe_Client("ltEr9IacPaOh2Cjn7xU5Gg%3D%3D", "ae869b3b2c8baefc38a15e0946e48efe").create()
    print(poe_client.subscription)


@pytest.mark.asyncio
async def test_explore_bots():
    poe_client = await Poe_Client("ltEr9IacPaOh2Cjn7xU5Gg%3D%3D", "ae869b3b2c8baefc38a15e0946e48efe").create()
    bots = await poe_client.explore_bots(count=100)
    print(bots)
    bots = await poe_client.explore_bots(explore_all=True)
    print(bots)


@pytest.mark.asyncio
async def test_get_available_bots():
    """after getting bots, the handle equals url_botname,examples in the next test"""
    poe_client = await Poe_Client("ltEr9IacPaOh2Cjn7xU5Gg%3D%3D", "ae869b3b2c8baefc38a15e0946e48efe").create()
    bots = await poe_client.get_available_bots(count=2)
    print(bots)
    bots = await poe_client.get_available_bots(get_all=True)
    print(bots)


@pytest.mark.asyncio
async def test_stream_ask():
    poe_client = await Poe_Client("ltEr9IacPaOh2Cjn7xU5Gg%3D%3D", "ae869b3b2c8baefc38a15e0946e48efe").create()
    async for message in poe_client.ask_stream(url_botname="ChatGPT", question="introduce openai",
                                               suggest_able=True):
        print(message, end="")
    chat_code = poe_client.bot_code_dict['ChatGPT'][0]
    print(poe_client.bots['ChatGPT']['chats'][chat_code]['Suggestion'])


@pytest.mark.asyncio
async def test_chatbreak():
    poe_client = await Poe_Client("ltEr9IacPaOh2Cjn7xU5Gg%3D%3D", "ae869b3b2c8baefc38a15e0946e48efe").create()
    bot, data = list(poe_client.bots.items())[0]
    chat = list(data['chats'].values())[0]
    await poe_client.send_chat_break(url_botname=bot, chat_code=chat['chatCode'])


@pytest.mark.asyncio
async def test_bot_operations():
    poe_client = await Poe_Client("ltEr9IacPaOh2Cjn7xU5Gg%3D%3D", "ae869b3b2c8baefc38a15e0946e48efe").create()
    # the handle when creating becomes the url_botname that to be used
    name1 = generate_random_str(10)
    name2 = generate_random_str(10)
    await poe_client.create_bot(handle=name1, prompt="a ai assistant")
    # change "test27gs" to test27gs2, and prompt changed too, but other config keep unchanged
    await poe_client.edit_bot(url_botname=name1, handle=name2, prompt="a computer programmer")
    # delete the bot by the new_name
    await poe_client.delete_bot(url_botname=name2)


@pytest.mark.asyncio
async def test_delete_available_bots():
    """caution, this will permanently delete your bots"""
    poe_client = await Poe_Client("ltEr9IacPaOh2Cjn7xU5Gg%3D%3D", "ae869b3b2c8baefc38a15e0946e48efe").create()
    name1 = generate_random_str(10)
    name2 = generate_random_str(10)
    name3 = generate_random_str(10)
    await poe_client.create_bot(handle=name1, prompt="a ai assistant")
    await poe_client.create_bot(handle=name2, prompt="a ai assistant")
    await poe_client.create_bot(handle=name3, prompt="a ai assistant")
    await poe_client.delete_available_bots(del_all=True)


@pytest.mark.asyncio
async def test_get_bot_data_and_info():
    poe_client = await Poe_Client("ltEr9IacPaOh2Cjn7xU5Gg%3D%3D", "ae869b3b2c8baefc38a15e0946e48efe").create()
    name1 = generate_random_str(10)
    await poe_client.create_bot(handle=name1, prompt="a ai assistant")
    data = await poe_client.get_botdata(url_botname=name1)
    print(data)
    info = await poe_client.get_bot_info(url_botname=name1)
    print(info)


name = generate_random_str(10)
chat_code = ""


@pytest.mark.asyncio
async def test_three_messages():
    global chat_code
    poe_client = await Poe_Client("ltEr9IacPaOh2Cjn7xU5Gg%3D%3D", "ae869b3b2c8baefc38a15e0946e48efe").create()
    await poe_client.create_bot(handle=name, prompt="a ai assistant")

    async for message in poe_client.ask_stream(url_botname=name, question="hello"):
        print(message, end="")
    chat_code = poe_client.bot_code_dict[name][0]
    async for message in poe_client.ask_stream(url_botname=name, question="hello", chat_code=chat_code,
                                               suggest_able=True):
        print(message, end="")
    async for message in poe_client.ask_stream(url_botname=name, question="hello", chat_code=chat_code):
        print(message, end="")


@pytest.mark.asyncio
async def test_delete_chats():
    poe_client = await Poe_Client("ltEr9IacPaOh2Cjn7xU5Gg%3D%3D", "ae869b3b2c8baefc38a15e0946e48efe").create()
    await poe_client.delete_chat_by_chat_code(chat_code)
    async for message in poe_client.ask_stream(url_botname=name, question="hello"):
        print(message, end="")
    async for message in poe_client.ask_stream(url_botname=name, question="hello"):
        print(message, end="")
    await poe_client.delete_chat_by_count("ChatGPT", del_all=True)
