import asyncio
import os
from telethon import TelegramClient, events, tl
import logging
logging.basicConfig(level=logging.INFO)

class cb:
    def __init__(self):
        # Permissions
        self.owner = int(os.environ["TELEGRAM_OWNER_ID"])
        self.control_channel = 288400190
        self.perms =    {
                            "set_header":       {self.owner},
                            "shutdown_switch":  {self.owner},
                            "source_code":      {"ALL"},
                            "picture_scrape":   {self.owner},
                        }

        # Default message reply header
        self.header = "`CoopBoop`"

        # Start
        ID = os.environ["TELEGRAM_API_ID"]
        hs = os.environ["TELEGRAM_API_HASH"]
        self.client = TelegramClient('gdynamics', ID, hs)
        print("Bot started")

    def perm(wrapped_handler):
        async def handler(self, event):
            auth = self.perms[wrapped_handler.__name__]
            sender = event.message.from_id
            if auth == {"ALL"} or sender in auth:
                print(sender, "permitted for", wrapped_handler.__name__)
                await wrapped_handler(self, event)
            else:
                print(event)
                print(sender, "denied for", wrapped_handler.__name__)
        return handler

    async def fmt_reply(self, event, msg):
        await event.reply(self.header + '\n' + msg)

    @perm
    async def set_header(self, event):
        cmd = event.message.text.split(' ')
        if(len(cmd) < 2):
            await self.fmt_reply(event, "Improper format for set_header!")
            return
        self.header = ' '.join(cmd[1:])
        await self.fmt_reply(event, "New header set")

    @perm
    async def shutdown_switch(self, event):
        print('Shutting down')
        await event.client.disconnect()

    @perm
    async def source_code(self, event):
        print("source_code")
        await self.fmt_reply(event, "https://github.com/coopervk/cb")

    @perm
    async def picture_scrape(self, event):
        cmd = event.message.raw_text.split(' ')
        if(len(cmd) != 2):
            await self.fmt_reply(event, "Improper format for picture_scrape!")
            return
        chat = int(cmd[1])

        print("picture_scrape", chat)
        async for image in self.client.iter_messages(chat, filter=tl.types.InputMessagesFilterPhotos):
            print(image.id)

    async def literally_everything(self, event):
        print("DEBUG:", event)

    def run(self):
        with self.client:
            # Register events
            print("Adding events")
            self.client.add_event_handler(self.shutdown_switch, events.NewMessage(pattern=';sid', chats=self.control_channel))
            self.client.add_event_handler(self.source_code, events.NewMessage(pattern=';source'))
            self.client.add_event_handler(self.picture_scrape, events.NewMessage(pattern=';pscrape'))
            self.client.add_event_handler(self.set_header, events.NewMessage(pattern=';set_header'))
            #self.client.add_event_handler(self.literally_everything)
            print("Events added")

            # Run bot
            self.client.run_until_disconnected()

if __name__ == "__main__":
    bot = cb()
    bot.run()
