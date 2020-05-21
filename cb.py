import asyncio
import os
from telethon import TelegramClient, events
import logging
#logging.basicConfig(level=logging.DEBUG)

async def shutdown_switch(event):
    print("Message received:", event.raw_text)
    if 'sid' in event.raw_text:
        print('Shutting down')
        await event.client.disconnect()

def main():
    ID = os.environ["TELEGRAM_API_ID"]
    hs = os.environ["TELEGRAM_API_HASH"]
    with TelegramClient('gdynamics', ID, hs) as client:
        print("Bot started")

        # Register events
        client.add_event_handler(shutdown_switch, events.NewMessage())
        print("Events added")

        # Run bot
        client.run_until_disconnected()

if __name__ == "__main__":
    main()
