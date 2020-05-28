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
                            "activity":         {self.owner},
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
        """ Decorator that forces each command to be checked via its name in self.perms{}
        """
        async def handler(self, event):
            auth = self.perms[wrapped_handler.__name__]
            sender = event.message.from_id
            if auth == {"ALL"} or sender in auth:
                self.bot_log(str(sender) + " permitted for " + wrapped_handler.__name__)
                await wrapped_handler(self, event)
            else:
                self.bot_log(str(sender) + " denied for " + wrapped_handler.__name__)
        return handler

    def name(self, entity, at=False):
        """ Get the name of the user in the format of FirstName LastName(@username)
        """
        if at:
            at = '@'
        else:
            at = ''

        if type(entity) is tl.types.User:
            if not entity.deleted:
                name = entity.first_name
                name += ' ' + entity.last_name if entity.last_name else ''
                name += '(' + at + entity.username + ')' if entity.username else ''
            else:
                name = "<Deleted Account>"
        else:
            name = entity.title

        return name

    def bot_log(self, log):
        """ Log the string log into the file self.bot_log_file, by default ./bot_log.txt
        """
        self.bot_log_file.write(datetime.now().isoformat() + " --> " + log + '\n')
        self.bot_log_file.flush()

    def str_to_datetime(self, time):
        """ Turn a string in format "year-month-dayThour:minute:second" into a datetime
        """
        fmt = "%Y-%m-%d"
        if ':' in time:
            fmt += "T%H:%M:%S"
        dt = datetime.strptime(time, fmt)
        return dt

    def datetime_to_str(self, dt):
        """ Turn a datetime into a string for format "year-month-dayThour:minute:second"
        """
        return datetime.strftime(dt, "%Y-%m-%dT%H:%M:%S")

    async def fmt_reply(self, event, msg):
        """ Reply to a message event (does not have to be an event) with the message msg
        """
        msg = self.header + '\n' + msg
        for i in range(0, len(msg), 4096):
            await event.reply(msg[i:i+4096])

    @perm
    async def set_header(self, event):
        """ Set the header of the bot at self.header to all text after ";hdr "
        -Supports text formatting (italic, monospace, etc)
        -Reply message to confirm header changed includes the new header in action

        Ex: ;hdr `John's Bot`
        """
        cmd = event.message.text.split(' ')
        if(len(cmd) < 2):
            await self.fmt_reply(event, "Improper syntax for set_header!")
            return
        self.header = ' '.join(cmd[1:])
        await self.fmt_reply(event, "New header set")
        self.bot_log("header set to " + self.header)

    @perm
    async def shutdown_switch(self, event):
        """ Shutdown the bot
        -First logs the shutdown and closes the logfile

        Ex: ;sid
        """
        self.bot_log("Shutting down")
        self.bot_log_file.close()
        await event.client.disconnect()

    @perm
    async def source_code(self, event):
        """ Return the link to the repository of this bot
        -Possibly required via AGPL3 for users, also good to just have transparancy

        Ex: ;src
        """
        await self.fmt_reply(event, "https://github.com/coopervk/cb")

    @perm
    async def scrape(self, event):
        """ Scrape (download) all media from a given chat/channel/group
        -Format: ;scrape chatID(optional)
        -Includes videos, youtube thumbnails, sometimes stickers, compressed and uncompressed photos, etc
        -Replies with details about how long it took and how many media it saved
        -May be useful to get the id of the dialog to scrape fist via ;id_of

        -Ex:    ;scrape
                ;scrape 12345678
        """
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
        await self.fmt_reply(message, elap + ", " + str(cnt) + " saved until this point.")

    @perm
    async def id_of(self, event):
        """ Get the numerical ID of a chat/channel/group via part of its name
        -Format: ;idof name
        -Goes through every single dialog
        -Replies with list of possible matches by name --> ID
        -Prepends list with "> "
        -Simply uses a match method of substring (Python's in keyword) of dialog.lower() vs self.name().lower()

        -Ex:    ;idof john
                ;idof linux-chat
        """
        cmd = event.message.raw_text.split(' ')
        if(len(cmd) < 2):
            await self.fmt_reply(event, "Improper syntax for ;idof! Need a name!")
            return

        name_arg = ' '.join(cmd[1:])
        name_pot = {}
        dialogs = await self.client.get_dialogs()
        for dialog in dialogs:
            name_dlg = self.name(dialog.entity)
            if name_arg.lower() in name_dlg.lower():
                name_pot[name_dlg] = dialog.entity.id

        if len(name_pot) == 0:
            await self.fmt_reply(event, "No matches found for " + name_arg)
        else:
            answer = ""
            for name, ID in name_pot.items():
                answer += "> " + name + " --> `" + str(ID) + "`" + '\n'
            await self.fmt_reply(event, answer)

    @perm
    async def activity(self, event):
        """ Return a list of the top 10 most active/inactive members since time provided (if any)
        -Format: ;activity choice date(optional) chatID(optional)
        -Choice can be active or inactive, can be shortened to a or i
        -Date is in format year-month-day or year-month-dayThour:minute:second
        -If you do not want to choose a date but you want a chat ID, use "none"
        -Uses UTC!
        -Chat ID can be discovered with ;idof
        -Useful for picking out "lurkers" and other suspicious users

        Ex:     ;activity active
                ;activity inactive 2020-05-30
                ;activity i none 10203040
        """
        cmd = event.message.raw_text.split(' ')
        cmd_len = len(cmd)

        if cmd_len > 1:
            choice = cmd[1][0].lower()
            dt = None
            if type(event.to_id) is tl.types.PeerChat:
                chat = event.to_id.chat_id
            elif type(event.to_id) is tl.types.PeerChannel:
                chat = event.to_id.channel_id
        if cmd_len > 2:
            if cmd[2].lower() != "none":
                dt = self.str_to_datetime(cmd[2])
            else:
                dt = None
        if cmd_len > 3:
            chat = int(cmd[3])
        if cmd_len < 2 or cmd_len > 4:
            await self.fmt_reply(event, "Improper syntax for ;activity! Need a type (active, inactive)")
            return

        members = {}
        async for member in self.client.iter_participants(chat):
            members[member.id] = [self.name(member), 0]

        async for msg in self.client.iter_messages(chat, offset_date=dt, reverse=(dt is not None)):
            if msg.from_id in members:
                members[msg.from_id][1] += 1

        sorted_members = members.values()
        sorted_members = sorted(sorted_members, key=lambda l:l[1], reverse=choice == 'a')

        choice = "most" if choice=='a' else "least"
        results = "The 10 " + choice + " active users"
        if dt:
            results += " since " + self.datetime_to_str(dt)
        results += " are:\n"
        for i in range(min(len(sorted_members),10)):
            results += "{:2d}".format(i+1) + ". " + sorted_members[i][0] + " --> " + str(sorted_members[i][1]) + '\n'

        await self.fmt_reply(event, results)

    async def literally_everything(self, event):
        """ Displays every single event the bot encounters for debugging or brainstorming
        -Should not be set by default, commented out below
        """
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
            self.client.add_event_handler(self.activity, events.NewMessage(pattern=';activity'))
            #self.client.add_event_handler(self.literally_everything)
            print("Events added")

            # Run bot
            self.client.run_until_disconnected()

if __name__ == "__main__":
    bot = cb()
    bot.run()
