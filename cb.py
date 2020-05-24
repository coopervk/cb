import asyncio
import os
from telethon import TelegramClient, events, tl
from datetime import datetime
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
                            "scrape":           {self.owner},
                            "id_of":            {self.owner},
                        }

        # Default message reply header
        self.header = "`CoopBoop`"

        # Set file to log bot activity to
        self.bot_log_file = open("./bot_log.txt", 'a')

        # File download location
        self.file_download_path = "./tmp"

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
                self.bot_log(str(sender) + " permitted for " + wrapped_handler.__name__)
                await wrapped_handler(self, event)
            else:
                self.bot_log(str(sender) + " denied for " + wrapped_handler.__name__)
        return handler

    def bot_log(self, log):
        self.bot_log_file.write(datetime.now().isoformat() + " --> " + log + '\n')
        self.bot_log_file.flush()

    async def fmt_reply(self, event, msg):
        await event.reply(self.header + '\n' + msg)

    @perm
    async def set_header(self, event):
        cmd = event.message.text.split(' ')
        if(len(cmd) < 2):
            await self.fmt_reply(event, "Improper syntax for set_header!")
            return
        self.header = ' '.join(cmd[1:])
        await self.fmt_reply(event, "New header set")
        self.bot_log("header set to " + self.header)

    @perm
    async def shutdown_switch(self, event):
        self.bot_log("Shutting down")
        self.bot_log_file.close()
        await event.client.disconnect()

    @perm
    async def source_code(self, event):
        await self.fmt_reply(event, "https://github.com/coopervk/cb")

    @perm
    async def scrape(self, event):
        cmd = event.message.raw_text.split(' ')
        if(len(cmd) != 2):
            chat = event.to_id.chat_id if type(event.to_id) is tl.types.PeerChat else event.to_id.user_id
        else:
            chat = int(cmd[1])

        self.bot_log("scrape " + str(chat))
        cnt = 0
        before = datetime.now()
        async for message in self.client.iter_messages(chat):
            if message.media is not None:
                await message.download_media(self.file_download_path)
                cnt += 1
        after = datetime.now()
        diff = (after - before).total_seconds()
        secs = str(int(diff % 60))
        mins = str(int(diff / 60))
        hrrs = str(int(diff / 3600))
        elap = hrrs + ":" + mins + ":" + secs
        await self.fmt_reply(message, elap + ", saved until this point.")

    @perm
    async def id_of(self, event):
        cmd = event.message.raw_text.split(' ')
        if(len(cmd) < 2):
            await self.fmt_reply(event, "Improper syntax for ;idof! Need a name!")
            return

        name_arg = ' '.join(cmd[1:])
        name_pot = {}
        dialogs = await self.client.get_dialogs()
        for dialog in dialogs:
            entity = dialog.entity
            if type(entity) is tl.types.User:
                if not entity.deleted:
                    name_dlg = entity.first_name
                    name_dlg += ' ' + entity.last_name if entity.last_name else ''
                    name_dlg += '(@' + entity.username + ')' if entity.username else ''
            else:
                name_dlg = entity.title
            if name_arg.lower() in name_dlg.lower():
                name_pot[name_dlg] = entity.id

        if len(name_pot) == 0:
            await self.fmt_reply(event, "No matches found for " + name_arg)
        else:
            answer = ""
            for name, ID in name_pot.items():
                answer += "> " + name + " --> `" + str(ID) + "`" + '\n'
            await self.fmt_reply(event, answer)

    async def literally_everything(self, event):
        print("DEBUG:", event)

    def run(self):
        self.bot_log("Started bot")

        with self.client:
            # Register events
            print("Adding events")
            self.client.add_event_handler(self.shutdown_switch, events.NewMessage(pattern=';sid', chats=self.control_channel))
            self.client.add_event_handler(self.source_code, events.NewMessage(pattern=';src'))
            self.client.add_event_handler(self.scrape, events.NewMessage(pattern=';scrape'))
            self.client.add_event_handler(self.set_header, events.NewMessage(pattern=';hdr'))
            self.client.add_event_handler(self.id_of, events.NewMessage(pattern=';idof'))
            #self.client.add_event_handler(self.literally_everything)
            print("Events added")

            # Run bot
            self.client.run_until_disconnected()

if __name__ == "__main__":
    bot = cb()
    bot.run()
