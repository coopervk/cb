"""
Launch Telethon based Telegram userbot
"""


import asyncio
from datetime import datetime
import json
import types
import logging
import os
import functools
import exif
from telethon import TelegramClient, events, tl, errors


logging.basicConfig(level=logging.INFO)


class CoopBoop:
    """ Driver class for the userbot
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    # pylint: disable=no-self-use

    def __init__(self):
        # Load from config file
        with open("config.json", "r") as config_file:
            config = json.load(config_file)

        # Permissions
        self.owner = config['owner']
        self.perms = config['perms']
        for command in self.perms:
            if self.perms[command]['whitelist'] == [ "OWNER" ]:
                self.perms[command]['whitelist'] = [ self.owner ]

        # Default message reply header
        self.header = config['header']

        # Set file to log bot activity to
        self.bot_log_file = open("./bot_log.txt", 'a')

        # File download location
        self.file_download_path = "./tmp/"

        # Set do not disturb to off by default
        self.dnd = False
        self.dnd_msg = config['dnd_msg'] if config['dnd_msg'] != "None" else None
        self.dnd_pic = config['dnd_pic'] if config['dnd_pic'] != "None" else None
        self.dnd_tracker = {}

        # Start
        self.api_id = config['api_id']
        self.api_hash = config['api_hash']
        self.owner_name = config['owner_name']
        self.client = TelegramClient(self.owner_name, self.api_id, self.api_hash)
        print("Bot started")


    def perm(wrapped_handler):
        """ Decorator that forces each command to be checked via its name in self.perms{}
        """
        # pylint: disable=no-self-argument
        # pylint: disable=not-callable
        # pylint: disable=no-member
        @functools.wraps(wrapped_handler)
        async def handler(self, event):
            auth = self.perms[wrapped_handler.__name__]['whitelist']
            xauth = self.perms[wrapped_handler.__name__]['blacklist']
            sender = event.message.from_id
            if sender:
                entity = await self.client.get_entity(sender)
                person = str(sender) + "(" + self.name(entity) + ")"
            else:
                person = "(N/A)"
            if not sender in xauth and (auth == ['ALL'] or sender in auth):
                self.bot_log(person + " permitted for " + wrapped_handler.__name__)
                await wrapped_handler(self, event)
            else:
                self.bot_log(person + " denied for " + wrapped_handler.__name__)
        return handler


    def name(self, entity, at_symbol=False):
        """ Get the name of the user in the format of FirstName LastName(@username)
        """
        if at_symbol:
            at_symbol = '@'
        else:
            at_symbol = ''

        if isinstance(entity, tl.types.User):
            if not entity.deleted:
                name = entity.first_name
                name += ' ' + entity.last_name if entity.last_name else ''
                name += '(' + at_symbol + entity.username + ')' if entity.username else ''
            else:
                name = "<Deleted Account>"
        else:
            name = entity.title

        return name


    def bot_log(self, log):
        """ Log the string log into the file self.bot_log_file, by default ./bot_log.txt
        """
        self.bot_log_file.write(self.datetime_to_str(datetime.now()) + " --> " + log + '\n')
        self.bot_log_file.flush()


    def str_to_datetime(self, time):
        """ Turn a string in format "year-month-dayThour:minute:second" into a datetime
        """
        fmt = "%Y-%m-%d"
        if ':' in time:
            fmt += "T%H:%M:%S"
        date = datetime.strptime(time, fmt)
        return date


    def datetime_to_str(self, date):
        """ Turn a datetime into a string for format "year-month-dayThour:minute:second"
        """
        return datetime.strftime(date, "%Y-%m-%dT%H:%M:%S")


    async def fmt_reply(self, event, msg):
        """ Reply to a message event (does not have to be an event) with the message msg
        """
        msg = self.header + '\n' + msg
        for i in range(0, len(msg), 4096):
            await event.reply(msg[i:i+4096])


    def exif_clean(self, image_name):
        """ Remove all exif data from the provided image
        """
        with open(image_name, 'rb') as image:
            image = exif.Image(image)
            if not image.has_exif:
                return None
            image.delete_all()
            clean_image_name = ''.join(image_name.split('.')[:-1]) + "_cleaned.jpg"
            with open(clean_image_name, 'wb') as cleaned_image:
                cleaned_image.write(image.get_file())
        return clean_image_name


    def exif_data(self, image_name):
        """ Return a dict of all the known information about the file
        """
        # pylint: disable=broad-except
        with open(image_name, 'rb') as image:
            image = exif.Image(image)
            if image.has_exif:
                exif_data = {}
                for prop in dir(image):
                    try:
                        val = getattr(image, prop)
                        if prop[0:1] != "_":
                            if not isinstance(val, types.MethodType):
                                exif_data[prop] = val
                    except Exception:
                        pass
                return exif_data
            return None


    async def map_pattern_to_event_method(self):
        """ Get dictionary mapping of commands to the methods they trigger
        -Commands are specified by setting a pattern when registering an event
        """
        mapping = {}
        for event_handler in self.client.list_event_handlers():
            pattern = event_handler[1].pattern
            if pattern is not None:
                method = event_handler[0]
                pattern = pattern.__self__.pattern[1:]
                mapping[pattern] = method
        return mapping


    def save_config(self, path="config.json"):
        """ Save the current state of the bot to the config file
        -Take extra care as to where you call this.
        -Don't hand it off to user input EVER: arbitrary file overwrite
        """
        config = {}

        config['owner'] = self.owner
        config['perms'] = self.perms
        config['header'] = self.header or "None"
        config['dnd_msg'] = self.dnd_msg or "None"
        config['dnd_pic'] = self.dnd_pic or "None"
        config['api_id'] = self.api_id 
        config['api_hash'] = self.api_hash
        config['owner_name'] = self.owner_name

        self.bot_log(f"Saving config to {path}")
        with open(path, "w") as config_file:
            json.dump(config, config_file, indent=4)
            self.bot_log(f"Config saved to {path}")


    @perm
    async def set_header(self, event):
        """ Set the header of the bot at self.header to all text after ";hdr "
        -Supports text formatting (italic, monospace, etc)
        -Reply message to confirm header changed includes the new header in action

        Ex: ;hdr `John's Bot`
        """
        cmd = event.message.text.split(' ')
        if len(cmd) < 2:
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
        self.save_config()
        self.bot_log("Shutting down")
        self.bot_log_file.close()
        await event.client.disconnect()


    @perm
    async def source_code(self, event):
        """ Return the link to the repository of this bot
        -Possibly required via AGPL3 for users, also good to just have transparancy

        Ex: ;src
        """
        await self.fmt_reply(event, "https://github.com/gdynamics/cb")


    @perm
    async def scrape(self, event):
        """ Scrape (download) all media from a given chat/channel/group
        -Format: ;scrape chatID(optional)
        -Includes videos, youtube thumbnails, sometimes stickers, (un/)compressed photos, etc
        -Replies with details about how long it took and how many media it saved
        -May be useful to get the id of the dialog to scrape fist via ;idof

        -Ex:    ;scrape
                ;scrape 12345678
        """
        cmd = event.message.raw_text.split(' ')
        if len(cmd) != 2:
            chat = event.to_id.chat_id if isinstance(event.to_id, tl.types.PeerChat) else \
                   event.to_id.user_id
        else:
            chat = int(cmd[1])

        self.bot_log("scrape " + str(chat))
        cnt = 0
        before = datetime.now()
        async for message in self.client.iter_messages(chat):
            if message.media is not None:
                try:
                    await message.download_media(self.file_download_path)
                    cnt += 1
                except errors.FloodWaitError as error:
                    await asyncio.sleep(error.seconds)
        after = datetime.now()
        diff = (after - before).total_seconds()
        secs = str(int(diff % 60))
        mins = str(int(diff / 60))
        hrrs = str(int(diff / 3600))
        elap = hrrs + ":" + mins + ":" + secs
        await self.fmt_reply(event, elap + ", " + str(cnt) + " saved until this point.")


    @perm
    async def id_of(self, event):
        """ Get the numerical ID of a chat/channel/group via part of its name
        -Format: ;idof name
        -Goes through every single dialog
        -Replies with list of possible matches by name --> ID
        -Prepends list with "> "
        -Simply uses a match method of substring (Python's in keyword) of dialog.lower() vs
         self.name().lower()

        -Ex:    ;idof john
                ;idof linux-chat
        """
        cmd = event.message.raw_text.split(' ')
        if len(cmd) < 2:
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
            for name, user_id in name_pot.items():
                answer += "> " + name + " --> `" + str(user_id) + "`" + '\n'
            await self.fmt_reply(event, answer)


    @perm
    async def name_of(self, event):
        """ Get the name which corresponds to a given ID
        -Format: ;name ID
        -A fancy wrapper around self.name()

        -Ex:    ;name 12345678
        """
        cmd = event.message.raw_text.split(' ')
        if len(cmd) < 2:
            await self.fmt_reply(event, "Improper syntax for ;name! Need an ID argument!")
            return

        try:
            entity = await self.client.get_entity(int(cmd[1]))
            name = self.name(entity)
            await self.fmt_reply(event, name)
        except ValueError:
            await self.fmt_reply(event, "Improper syntax for ;name! Argument was not an ID")


    @perm
    async def activity(self, event):
        """ Return a list of the top 10 most active/inactive members since time provided (if any)
        -Format: ;activity choice date(optional) chatID(optional) results_count(optional)
        -choice         --> active or inactive, can be shortened to a or i
        -date           --> time in format year-month-day or year-month-dayThour:minute:second,
                            uses UTC, can be none
        -chatID         --> id of chat you want to check the activity in, can be none, can find
                            chat IDs with ;idof
        -results_count  --> number of results you want, either a number or "all"

        -Useful for picking out "lurkers" and other suspicious users

        Ex:     ;activity active
                ;activity inactive 2020-05-30
                ;activity i none 10203040
                ;activity i 2020-05-30 10203040 100
                ;activity i 2020-05-30 none all
        """
        # pylint: disable=too-many-branches
        cmd = event.message.raw_text.split(' ')
        cmd_len = len(cmd)

        if cmd_len < 2 or cmd_len > 5:
            await self.fmt_reply(event, "Improper syntax for ;activity! Need a type")
            return
        if cmd_len > 1:
            choice = cmd[1][0].lower()
            date = None
            results_count = 10
            if isinstance(event.to_id, tl.types.PeerChat):
                chat = event.to_id.chat_id
            elif isinstance(event.to_id, tl.types.PeerChannel):
                chat = event.to_id.channel_id
        if cmd_len > 2:
            if cmd[2].lower() != "none":
                date = self.str_to_datetime(cmd[2])
            else:
                date = None
        if cmd_len > 3:
            if cmd[3].lower() != "none":
                chat = int(cmd[3])
        if cmd_len > 4:
            if cmd[4].lower() == "all":
                results_count = "all"
            else:
                results_count = int(cmd[4])

        members = {}
        async for member in self.client.iter_participants(chat):
            members[member.id] = [self.name(member), 0]

        async for msg in self.client.iter_messages(chat, offset_date=date, \
                                                   reverse=(date is not None)):
            if msg.from_id in members:
                members[msg.from_id][1] += 1

        sorted_members = members.values()
        sorted_members = sorted(sorted_members, key=lambda l:l[1], reverse=choice == 'a')

        if results_count == "all":
            results_count = len(sorted_members)

        choice = "most" if choice=='a' else "least"
        results = "The " + str(results_count) + " " + choice + " active users"
        if date:
            results += " since " + self.datetime_to_str(date)
        results += " are:\n"
        for i in range(min(len(sorted_members),results_count)):
            results += "{:2d}".format(i+1) + ". " + sorted_members[i][0] + \
                       " --> " + str(sorted_members[i][1]) + '\n'

        await self.fmt_reply(event, results)


    @perm
    async def do_not_disturb(self, event):
        """ Turn on or off do not disturb mode or set the do not disturb mode picture
        -on: Turn on
        -off: Turn off
        -set: Set the dnd mode image to the following message

        Ex: ;dnd on
            ;dnd off
            ;dnd set Please leave me alone
        """
        cmd = event.message.raw_text.split(' ')
        cmd_len = len(cmd)
        if cmd_len == 1 or cmd_len > 3:
            await self.fmt_reply(event, "Improper syntax for do_not_disturb!")
            return
        if cmd[1].lower() == "on":
            self.dnd = True
            await self.fmt_reply(event, "Do not disturb: `Enabled`")
        elif cmd[1].lower() == "off":
            self.dnd = False
            await self.fmt_reply(event, "Do not disturb: `Disabled`")
        elif cmd[1].lower() == "set":
            cmd = ' '.join(cmd[2:])
            self.dnd_msg = cmd
            await self.fmt_reply(event, "Do not disturb message set")


    async def do_not_disturb_responder(self, event):
        """ Helper function for responding to messages when do not disturb is set
        -Replies when receiving a private message or when "mentioned" in a chat/channel
        -Only replies if the person hasn't gotten dnd'd recently (default 10 mins)
        """
        # pylint: disable=no-value-for-parameter
        if self.dnd:
            if isinstance(event.to_id, tl.types.PeerUser) or event.mentioned:
                now = datetime.now()
                sender = event.message.from_id

                if sender in self.dnd_tracker:
                    before = self.dnd_tracker[sender]
                    diff = (now - before).total_seconds()
                    mins = int(diff / 60)
                else:
                    mins = None

                if mins is None or mins > 10:
                    if self.dnd_msg is not None:
                        await self.fmt_reply(self.dnd_msg)
                    else:
                        await event.reply(file=self.dnd_pic)

                    self.dnd_tracker[sender] = now


    @perm
    async def exif(self, event):
        """ Remove or return the data from a JPEG/.jpg file.
        -Ex:  ;exif clean
              ;exif data
        -Must provide thumbnailed/uncompressed JPEG/.jpg file (no support for TIFF yet)
        -Command must be the "description"/accompanying message of the uploaded image
        """
        # pylint: disable=too-many-branches
        cmd = event.message.raw_text.split(' ')

        if len(cmd) != 2:
            await self.fmt_reply(event, "improper syntax for exif!")
        elif event.message.media is None:
            await self.fmt_reply(event, "No image given!")
        elif not isinstance(event.message.media, tl.types.MessageMediaDocument):
            await self.fmt_reply(event, "Did not send image as file!")
        elif event.message.media.document.mime_type != "image/jpeg":
            await self.fmt_reply(event, "This bot only supports JPEG/.jpg")
        else:
            try:
                image_provided = await event.message.download_media(self.file_download_path)
            except errors.FloodWaitError as error:
                await asyncio.sleep(error.seconds)

            if cmd[1] == "clean":
                clean_image = self.exif_clean(image_provided)
                if clean_image is None:
                    await self.fmt_reply(event, "Image never had exif data!")
                else:
                    clean_image_path = os.path.join(self.file_download_path, clean_image)
                    await event.reply(file=clean_image_path, force_document=True)
                    os.remove(image_provided)
                    os.remove(clean_image_path)
            elif cmd[1] == "data":
                exif_data = self.exif_data(image_provided)
                if exif_data is None:
                    await self.fmt_reply(event, "Image never had exif data!")
                else:
                    accumulator_str = ""
                    for exif_prop, exif_val in exif_data.items():
                        accumulator_str += f"**{exif_prop}**: {exif_val}\n"
                    await self.fmt_reply(event, accumulator_str)
                    os.remove(image_provided)
            else:
                await self.fmt_reply(event, "Improper syntax for exif!")


    @perm
    async def help(self, event):
        """ Print out either the list of commands or the docstring for a provided command
        -Format: ;help command_name(optional)

        -Ex:  ;help
              ;help exif
              ;help ;dnd
        """

        cmd = event.message.raw_text.split(' ')
        mapping = await self.map_pattern_to_event_method()

        if len(cmd) == 1:
            command_list = "**Commands:**\n"
            for command in mapping.keys():
                command_list += f"- ;{command}\n"
            await self.fmt_reply(event, command_list)
        elif len(cmd) == 2:
            command = cmd[1]
            if ';' in command:
                command = command[1:]
            if command not in mapping.keys():
                await self.fmt_reply(event, f"Command {command} does not exist!")
            else:
                await self.fmt_reply(event, f"{mapping[command].__doc__}")
        else:
            await self.fmt_reply(event, "Improper syntax for help!")


    async def literally_everything(self, event):
        """ Displays every single event the bot encounters for debugging or brainstorming
        -Should not be set by default, commented out below
        """
        print("DEBUG:", event)


    def run(self):
        """ Start the bot
        -Done here instead of init because of issues with calling async functions from non-async
         context, requiring the use of run_until_disconnected()
        """
        self.bot_log("Started bot")

        with self.client:
            # Register events
            print("Adding events")
            self.client.add_event_handler(self.shutdown_switch, events.NewMessage(pattern=';sid'))
            self.client.add_event_handler(self.source_code, events.NewMessage(pattern=';src'))
            self.client.add_event_handler(self.scrape, events.NewMessage(pattern=';scrape'))
            self.client.add_event_handler(self.set_header, events.NewMessage(pattern=';hdr'))
            self.client.add_event_handler(self.id_of, events.NewMessage(pattern=';idof'))
            self.client.add_event_handler(self.name_of, events.NewMessage(pattern=';name'))
            self.client.add_event_handler(self.activity, events.NewMessage(pattern=';activity'))
            self.client.add_event_handler(self.do_not_disturb, events.NewMessage(pattern=';dnd'))
            self.client.add_event_handler(self.do_not_disturb_responder, \
                                          events.NewMessage(incoming=True))
            self.client.add_event_handler(self.exif, events.NewMessage(pattern=';exif'))
            self.client.add_event_handler(self.help, events.NewMessage(pattern=';help'))
            #self.client.add_event_handler(self.literally_everything)
            print("Events added")

            # Run bot
            self.client.run_until_disconnected()


if __name__ == "__main__":
    bot = CoopBoop()
    bot.run()
