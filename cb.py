import asyncio
import os
from telethon import TelegramClient, events
import logging
logging.basicConfig(level=logging.INFO)

class cb:
    def __init__(self):
        # Permissions
        self.perms =    {
                            "shutdown_switch":  {int(os.environ["TELEGRAM_OWNER_ID"])},
                            "source_code":      {"ALL"}
                        }

        ID = os.environ["TELEGRAM_API_ID"]
        hs = os.environ["TELEGRAM_API_HASH"]
        self.client = TelegramClient('gdynamics', ID, hs)
        print("Bot started")

    def perm(wrapped_handler):
        async def handler(self, event):
            auth = self.perms[wrapped_handler.__name__]
            sender = event.message_from_id
            if auth == {"ALL"} or sender in auth:
                print(sender, "permitted for", wrapped_handler.__name__)
                await wrapped_handler(self, event)
            else:
                print(sender, "denied for", wrapped_handler.__name__)
        return handler

    @perm
    async def shutdown_switch(self, event):
        print('Shutting down')
        await event.client.disconnect()

    @perm
    async def source_code(self, event):
        print("source_code")
        await event.reply("https://github.com/coopervk/cb")

    async def literally_everything(self, event):
        print("DEBUG:", event)

    def run(self):
        with self.client:
            # Register events
            print("Adding events")
            self.client.add_event_handler(self.shutdown_switch, events.NewMessage(pattern=';sid', chats=288400190))
            self.client.add_event_handler(self.source_code, events.NewMessage(pattern=';source'))
            #self.client.add_event_handler(self.literally_everything)
            print("Events added")

            # Run bot
            self.client.run_until_disconnected()

if __name__ == "__main__":
    bot = cb()
    bot.run()
