import asyncio
import os
from telethon import TelegramClient, events
import logging
#logging.basicConfig(level=logging.DEBUG)



async def shutdown_switch(event):
    print('Shutting down')
    await event.client.disconnect()

async def source_code(event):
    await event.reply("https://github.com/coopervk/cb")

def main():
    ID = os.environ["TELEGRAM_API_ID"]
    hs = os.environ["TELEGRAM_API_HASH"]
    with TelegramClient('gdynamics', ID, hs) as client:
        print("Bot started")

        # Register events
        client.add_event_handler(shutdown_switch, events.NewMessage(pattern=';sid', chats=288400190))
        client.add_event_handler(source_code, events.NewMessage(pattern=';source'))
        print("Events added")

        # Run bot
        client.run_until_disconnected()

if __name__ == "__main__":
    main()
