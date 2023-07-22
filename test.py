import pytest

from async_poe_client import Poe_Client


@pytest.mark.asyncio
async def test_get_subscription_info():
    poe_client = await Poe_Client("your p_b token").create()
    print(poe_client.subscription)


@pytest.mark.asyncio
async def test_explore_bots():
    poe_client = await Poe_Client("your p_b token").create()
    bots = await poe_client.explore_bots(count=100)
    print(bots)
    bots = await poe_client.explore_bots(explore_all=True)
    print(bots)


@pytest.mark.asyncio
async def test_get_available_bots():
    """after getting bots, the handle equals url_botname,examples in the next test"""
    poe_client = await Poe_Client("your p_b token").create()
    bots = await poe_client.get_available_bots(count=2)
    print(bots)
    bots = await poe_client.get_available_bots(get_all=True)
    print(bots)


@pytest.mark.asyncio
async def test_stream_ask():
    poe_client = await Poe_Client("xGle8cZ_Nlo2fyEgpmpPrA%3D%3D").create()
    bots = await poe_client.get_available_bots(count=2)
    async for message in poe_client.ask_stream(url_botname=bots[0]['handle'], question="introduce websockets",
                                               suggest_able=True):
        print(message, end="")


@pytest.mark.asyncio
async def test_httponly_ask():
    poe_client = await Poe_Client("your p_b token").create()
    answer = await poe_client.ask(url_botname="Assistant", question="Introduce openai")
    print(answer)


@pytest.mark.asyncio
async def test_chatbreak():
    poe_client = await Poe_Client("your p_b token").create()
    await poe_client.send_chat_break(url_botname="Assistant")


@pytest.mark.asyncio
async def test_bot_operations():
    poe_client = await Poe_Client("your p_b token").create()
    # the handle when creating becomes the url_botname that to be used
    await poe_client.create_bot(handle="test27gs", prompt="a ai assistant")
    # change "test27gs" to test27gs2, and prompt changed too, but other config keep unchanged
    await poe_client.edit_bot(url_botname="test27gs", handle="test27gs2", prompt="a computer programmer")
    # delete the bot by the new_name
    await poe_client.delete_bot(url_botname="test27gs2")


@pytest.mark.asyncio
async def test_delete_available_bots():
    """caution, this will permanently delete your bots"""
    poe_client = await Poe_Client("xGle8cZ_Nlo2fyEgpmpPrA%3D%3D").create()
    await poe_client.delete_available_bots(count=2)
    await poe_client.delete_available_bots(del_all=True)


@pytest.mark.asyncio
async def test_get_bot_data_and_info():
    poe_client = await Poe_Client("your p_b token").create()
    data = await poe_client.get_botdata(url_botname="578feb1716fe43f")
    print(data)
    config = await poe_client.get_bot_info(url_botname="578feb1716fe43f")
    print(config)


@pytest.mark.asyncio
async def test_del_some_conversations():
    poe_client = await Poe_Client("your p_b token").create()
    await poe_client.delete_bot_conversation(url_botname="Assistant", count=2)
    await poe_client.delete_bot_conversation(url_botname="Assistant", del_all=True)


@pytest.mark.asyncio
async def test_del_all_conversation():
    """caution, this will delete all the conversation with all bots"""
    poe_client = await Poe_Client("your p_b token").create()
    await poe_client.delete_all_conversations()


@pytest.mark.asyncio
async def test_history_messages():
    poe_client = await Poe_Client("your p_b token").create()
    messages = await poe_client.get_message_history(url_botname="GPT-4", count=20)
    print(messages)
    messages = await poe_client.get_message_history(url_botname="GPT-4", get_all=True)
    print(messages)
