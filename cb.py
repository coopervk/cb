import asyncio
import os
import logging
from telethon import TelegramClient

async def main():
    me = await client.get_me()

    # Send messages
    await client.send_message(me, "test")

if __name__ == "__main__":
    # Init
    ID = os.environ["TELEGRAM_API_ID"]
    hs = os.environ["TELEGRAM_API_HASH"]
    with TelegramClient('gdynamics', ID, hs) as client:
        client.loop.run_until_complete(main())
