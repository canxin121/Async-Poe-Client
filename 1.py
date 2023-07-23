import asyncio

from async_poe_client import Poe_Client


async def main():
    poe_client = await Poe_Client("l_recO0QgugqEyfgMbEt-g%3D%3D").create()
    # bots = await poe_client.get_available_bots(count=2)
    async for message in poe_client.ask_stream(url_botname="ChatGPT", question="hello",
                                               suggest_able=True):
        print(message, end="")


asyncio.run(main())
