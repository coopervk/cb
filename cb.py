import asyncio
import os
from telethon import TelegramClient, events
import logging
#logging.basicConfig(level=logging.DEBUG)

perms = {}

def perm(wrapped_handler):
    async def handler(event):
        auth = perms[wrapped_handler.__name__]
        if auth == {"ALL"} or event.message.from_id in auth:
            await wrapped_handler(event)
    return handler

@perm
async def shutdown_switch(event):
    print('Shutting down')
    await event.client.disconnect()

@perm
async def source_code(event):
    await event.reply("https://github.com/coopervk/cb")

def main():
    # Permissions
    perms["shutdown_switch"] = {os.environ["TELEGRAM_OWNER_ID"]}
    perms["source_code"] = {"ALL"}

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
