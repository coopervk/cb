# CoopBoop

## Overview
Telethon based Telegram userbot

## Get it running
1. Install the Telethon and exif libraries `pip install telethon exif`
2. Create a Telegram App at https://my.telegram.org/apps
3. Save the API_id and API_hash to their associated fields in config.json
4. Launch bot with `python cb.py` on Linux or `py cb.py` on Windows
5. Put in your phone number in the same format as you did on https://my.telegram.org/
6. Provide the code once it arrives
7. Create an empty "Control" group in Telegram
8. Send `;idof USERNAME` with your username (@)
9. Paste the number into the owner field of creds.json
10. Stop the bot by sending ";sid"
11. Set the whitelist of "id_of" to "OWNER" in config.json

## Bot features
### Security
Each command has an associated permission as to who can use it enforced through the decorator function perm.

Currently, you must update it manually. Generally, it's best to stick with self.owner, though feel free to add individuals you trust by their ID.

You can `tail -f bot_log.txt` to watch bot run in real time

For the function save_config, never pass user input as the arg. This could result in arbitrary file overwrite.

### Commands
See a more in depth explanation of each function in the associated docstring

(command, function, description)
1. ;sid, shutdown_switch, Shutdown the bot
2. ;src, source_code, Return link to source code of this bot. Update if you fork
3. ;scrape, scrape, Scrape every piece of media from a given chat or channel, returning details upon completion
4. ;hdr, set_header, Set the header for the formatted replies the bot gives
5. ;idof, id_of, Get the ID of every user whose name or username matches a given string by basic "in" compare
6. ;name, name_of, Get the name & username from a given ID (useful for tracking down people in log file)
7. ;activity, activity, Find the most or least common posters since a given date. Default 10
8. ;dnd, do_not_disturb, Enable/disable/set message for do not disturb mode. Defaults to only 1 message per ID in 10 mins to prevent spam
9. ;exif, exif, Get(data)/remove(clean) the exif data from a provided JPEG/.jpg image
10. ;help, help, Respond to user with list of commands or help for specified command (docstring)
11. ;perman, manage_permissions, manage or print the permissions for commands for the userbot

### Customization

You can change things like the header, do not display message, etc by using the commands themselves.

Currently changes made do not persist between runs unless changes in code directly.
