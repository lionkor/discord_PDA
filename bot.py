# Author @lionkor on github.com
#
# ---
#
# MIT License
#
# Copyright (c) 2019 Lion Kortlepel
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import discord
from datetime import datetime
import random
import calc
import json

COMMAND_NOT_AVAIL_IN_DMS = "Can't use this command in DMs (yet). If you'd like this feature to be added, contact the developer (`hello` command has more info about that)."

def time_str ():
    dtn = datetime.now ()
    return str (dtn.date ()) + " " + str (dtn.hour) + ":" + str (
        dtn.minute) + ":" + str (dtn.second)

def log (msg):
    time = time_str ()
    print (time + " [LOG] " + str (msg))
    print (time + " [LOG] " + str (msg), file = open ("log.txt", "a"))


kprefix = "prefix"
kpoll_channel = "poll_channel"
kdisabled_commands = "disabled_commands"

class Bot (discord.Client):
    default_prefix = "+"
    default_disabled_commands = []
    default_poll_channel = -1
    # TODO setting for enable/disable automatic help display

    default_config = {
        kprefix : default_prefix,
        kpoll_channel : default_poll_channel,
        kdisabled_commands : default_disabled_commands,
    }

    configs: {discord.Guild.id : {}} = dict ()

    def configs_load (self):
        with open ("cfgs.json", "r") as conf:
            temp = json.loads (conf.read ())
        for k, d in temp.items ():
            # conversion from strings to python objects
            self.configs[int (k)] = {
                kprefix : d[kprefix],
                kpoll_channel : d[kpoll_channel],
                kdisabled_commands : d[kdisabled_commands]
            }

    def configs_save (self):
        with open ("cfgs.json", "w+") as conf:
            conf.write (json.dumps (self.configs))

    def get_prefix (self, message: discord.Message): # string
        """
        helper method for finding the currently valid prefix
        """
        if message.guild is None:
            # is not a server text channel, so default prefix applies
            return self.default_prefix
        else:
            # get server prefix from config
            return self.configs[message.guild.id][kprefix]

    async def com_help (self, msg: str, message: discord.Message):
        # use long-help.json for per-command help, otherwise short-help.json

        prefix = self.get_prefix (message)

        with open ("short-help.json", "r") as shelp:
            obj: {str : dict} = json.load (shelp)

        if len (msg) != 0:
            with open ("long-help.json", "r") as lhelp:
                obj: {str: dict} = json.load (lhelp)
            # user is asking for detailed help
            if msg not in obj.keys ():
                return f"I can't find any help for command `{msg.replace ('`', '')}`. Type `{prefix}help` for a list of commands."
            else:
                return f"{message.author.mention}, here's help for `{msg}`:\n" \
                    f"**> __Aliases__**: \n{obj[msg]['alias']}\n\n" \
                    f"**> __Arguments__**: \n{obj[msg]['args']}\n\n" \
                    f"**> __Explanation__**: \n{obj[msg]['expl']}\n\n" \
                    f"**> __Example__**: \n{obj[msg]['exmp']}\n\n" \
                    f"*(note: don't actually type the `<>` and `[]` in the arguments. `<>` means argument is required, `[]` means it's optional.)*"

        fullhelp = "**PDA Help**\n" \
                   f"\n**Prefix is `{prefix}`.**\n" \
            f"For more detailed help about a command, type `{prefix}help command`.\n\n"

        for command, opt in obj.items ():
            if opt["args"] != "": # TODO fix this whole mess
                fullhelp += "`" + prefix + command + "`  `" + opt["args"] + "` -- " + opt['expl']
            else:
                fullhelp += "`" + prefix + command + "` -- " + opt['expl']
            if opt["alias"] != "":
                fullhelp += " - has aliases: " + opt["alias"]
            fullhelp += "\n"


        return fullhelp

    async def com_capify (self, msg: str, message: discord.Message):
        if len (msg) == 0:
            return "Whoops, invalid arguments!\n\n" + (await self.com_help ("capify", message))
        
        msg = msg.replace ("@everyone", "@ everyone").replace ("@here",
                                                               "@ here")
        result = ""
        u_case = bool (random.randint (0, 1))
        for c in msg:
            if u_case:
                result += c.upper ()
            else:
                result += c.lower ()
            u_case = not u_case
        if message.guild is not None:
            # deleting the message (feature requested by users)
            await message.delete ()
            return f"{message.author.mention}**:** {result}"
        else:
            # no deletion, username in DMs
            return f"{result}"

    async def com_spoilerize (self, msg: str, message: discord.Message):
        if len (msg) == 0:
            return "Whoops, invalid arguments!\n\n" + (await self.com_help ("spoilerize", message))

        msg = msg.replace ("@everyone", "@ everyone").replace ("@here",
                                                               "@ here")
        result = ""
        for c in msg:
            result += "||" + c + "||"
        return "```{0}```".format (result)

    def guilds_list_str (self, lst: list):
        result = ""
        for item in lst:
            result += "\"" + item.name + "\""
            if item != lst[len (lst) - 1]:
                result += ", "
        return result

    async def com_prefix (self, msg: str, message: discord.Message):
        if len (msg) == 0:
            return "Whoops, invalid arguments!\n\n" + (await self.com_help ("prefix", message))

        if message.guild is None:
            return COMMAND_NOT_AVAIL_IN_DMS
        else:
            if not message.author.guild_permissions.administrator:
                return f"{message.author.mention}, you must be administrator to use. Sorry!"
            self.configs[message.guild.id][kprefix] = msg
            return "Prefix set to `" + self.configs[
                message.guild.id][kprefix] + "`"

    async def com_thanks (self, content, message: discord.Message):
        with open ("thanks.txt", "a") as f:
            f.write (f"{time_str ()} {message.author.id} ({message.author}) thanked me in \"{message.channel}\" (guild \"{message.guild}\")! Custom message: thanks {content}\n")
        return f"Noted! I appreciate it {message.author.mention} :)" # TODO add random emoji

    async def com_vote (self, content: str, message: discord.Message): # refactor
        if message.guild is None:
            return COMMAND_NOT_AVAIL_IN_DMS
        else:
            if not message.author.guild_permissions.administrator:
                return f"{message.author.mention}, you must be administrator to use. Sorry!"
            # must mention a channel
            if len (message.channel_mentions) == 0:
                return "Must mention a channel, try again."
            # now message.channel_mentions[0] is the channel to send vote in
            msg: discord.Message = (await message.channel_mentions[0].send (
                content = content[content.find (" "):]))
            await msg.add_reaction (u"\U0001F53C")
            await msg.add_reaction (u"\U0001F53D")

    async def com_coinflip (self, content: str, message: discord.Message):
        if random.randint (0, 1) == 0:
            return "Heads!"
        else:
            return "Tails!"

    async def com_rng (self, content: str, message: discord.Message):
        # TODO help on no args given
        numbers = content.split (" ")
        if len (numbers) != 2:
            return "Whoops, invalid arguments!\n\n" + (await self.com_help ("rng", message))

        try:
            _min = int (numbers[0])
            _max = int (numbers[1])
        except Exception as e:
            log (str (e))
            return "Make sure both arguments are _whole_ numbers!"
        return "RNG: " + str (
            random.randint (min (_min, _max), max (_min, _max)))

    async def com_font (self, content: str, message: discord.Message):
        content = content.replace ("@everyone", "@ everyone").replace ("@here",
                                                                       "@ here")
        fonts = {
            "nice": " 𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜𝐵𝒞𝒟𝐸𝐹𝒢𝐻𝐼𝒥𝒦𝐿𝑀𝒩𝒪𝒫𝒬𝑅𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫𝟢"
                    "+-/*.,!?_#+",
            "mono": " 𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝟷𝟸𝟹𝟺𝟻"
                    "𝟼𝟽𝟾𝟿𝟶+-/*.,!?_#+",
            "circle": " ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩⒶⒷⒸⒹⒺ"
                      "ⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ①②③④⑤⑥⑦⑧⑨⓪"
                      "+-/*.,!?_#+",
            "super": " ᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᵠᴿˢᵀᵁⱽᵂˣˣʸᶻʸᶻ"
                     "¹²³⁴⁵⁶⁷⁸⁹⁰⁺⁻/*.,!?_#⁺",
            "tiny": " ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢABCDEFGHIJKLMNOPQRSTUVWXXYZYZ1"
                    "234567890+-/*.,!?_#+",
            "fraktur": " 𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ123456"
                       "7890+-/*.,!?_#+",
        }
        normal_font = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" \
                      "1234567890+-/*.,!?_#+"

        if content.split (" ")[0] not in fonts:
            return "Whoops, invalid arguments!\n\n" + (await self.com_help ("font", message))
        font_data: str = fonts[content.split (" ")[0]]
        new_content = ""
        log (content[content.find (" "):])
        for c in content[content.find (" "):]:
            index = normal_font.find (c)
            if index < 0:
                new_content += c
            else:
                new_content += font_data[index]
        log (new_content)
        return new_content

    # 0 = thing to compliment
    # 1 = user mention
    praises_first = [
        "I really love your {0}, {1}!",
        "Damn, {1}, I love your {0} so much :O",
        "Your {0} makes my heart melt omg {1}",
        "Ay {1}, I  a d o r e  your {0} <3",
        "{1}, you have the nicest {0}!!"
        # TODO add more
    ]

    praises_second = [
        "eyes", "hair", "voice", "way of speaking",
    ]

    async def com_praise (self, content: str, message: discord.Message):
        if len (message.mentions) == 0:
            return "Please mention someone that should be praised"
        _first : str  = random.choice (self.praises_first)  # main part of the message
        _second : str = random.choice (self.praises_second) # thing to compliment
        return _first.format (_second, message.mentions[0].mention)

    async def com_poll (self, content: str, message: discord.Message):
        content = content.replace ("@everyone", "@ everyone").replace ("@here",
                                                                       "@ here")
        
        if len (content) == 0:
            return "Whoops, invalid arguments!\n\n" + (await self.com_help ("poll", message))
        
        if message.guild is None:
            return COMMAND_NOT_AVAIL_IN_DMS
        else:
            if self.configs[message.guild.id][kpoll_channel] == -1:
                return f"{message.author.mention}, no poll channel is set. Use `{self.get_prefix (message)}settings set {kpoll_channel} <channel>` as " \
                    f"administrator to set up a poll channel. It is recommended to make this channel read-only for normal " \
                    f"users, and to disable reactions. To disable polls completely, use the `disable` command." # TODO make automatic setup possible
            channel: discord.TextChannel = message.guild.get_channel (
                self.configs[message.guild.id][kpoll_channel])
            msg: discord.Message = (
                await channel.send (content = content + " (by {0})".format (
                    message.author.mention)))
            await msg.add_reaction (u"\U0001F53C")
            await msg.add_reaction (u"\U0001F53D")
            await message.delete () # remove original message (requested by users)

    async def com_calculate (self, content: str, message: discord.Message):
        if len (content) == 0 or content == "":
            return "Whoops, invalid arguments!\n\n" + (await self.com_help ("calculate", message))
        try:
            res = calc.evaluate (content)
        except Exception as e:
            return f"Invalid calculation: {e}".replace ("float", "number").replace ("string", "characters")
        if content.find ("=") == -1:
            return f"```fix\n{content} = {res}```" # fix would mess up with multiple '='
        return f"```py\n{content} = {res}```"

    async def com_hello (self, content: str, message: discord.Message):
        prefix = self.default_prefix
        if message.guild is not None:
            prefix = self.configs[message.guild.id][kprefix]
        return f"Hello, {message.author.display_name}! I am this server's **P**ersonal **D**igital **A**ssistant, PDA. " \
            f"You can get a list of commands by typing `{prefix}help`. An admin can enable and disable any command with " \
            f"`{prefix}enable <command>` and `{prefix}disable <command>`. My author is **Harold#4650**, so talk to him if " \
            f"you have any feature requests, questions or problems, or use the poll below! \n\nMy code is here: " \
            f"<https://github.com/lionkor/discord_PDA>. \n\nHere's a short poll about me: <https://forms.gle/WeJ9JqDABEsAyVhL8>."

    async def com_enable (self, content: str, message: discord.Message):
        if len (content) == 0:
            return "Whoops, invalid arguments!\n\n" + (await self.com_help ("enable", message))
        if message.guild is not None:
            if not message.author.guild_permissions.administrator:
                return f"{message.author.mention}, you must be administrator to use. Sorry!"
        if message.guild is None:
            return COMMAND_NOT_AVAIL_IN_DMS
        if content not in self.commands:
            return f"I do not know the command `{content}`."
        if content not in self.configs[message.guild.id][kdisabled_commands]:
            return f"`{content}` is not disabled."
        ret = "Enabled the following commands: "
        disable_fn = self.commands[content]
        for s, fn in self.commands.items ():
            if fn == disable_fn:
                self.configs[message.guild.id][kdisabled_commands].remove (s)
                ret += "`" + s + "`, "
        return ret.rstrip (", ") + "."

    async def com_disable (self, content: str, message: discord.Message):
        if len (content) == 0:
            return "Whoops, invalid arguments!\n\n" + (await self.com_help ("disable", message))
        if message.guild is not None:
            if not message.author.guild_permissions.administrator:
                return f"{message.author.mention}, you must be administrator to use. Sorry!"
        if message.guild is None:
            return COMMAND_NOT_AVAIL_IN_DMS
        if content not in self.commands:
            return f"I do not know the command `{content}`."
        if content == "disable" or content == "enable":
            return f"For safety reasons it is not allowed to disable `{content}`."
        if content in self.configs[message.guild.id][kdisabled_commands]:
            return f"`{content}` and all aliases of it are already disabled."
        ret = "Disabled the following commands: "
        disable_fn = self.commands[content]
        for s, fn in self.commands.items ():
            if fn == disable_fn:
                self.configs[message.guild.id][kdisabled_commands].append (s)
                ret += "`" + s + "`, "
        return ret.rstrip (", ") + "."


    async def com_invite (self, content: str, message: discord.Message):
        return f"To invite me to your server, use this link: <https://discordapp.com/oauth2/authorize?client_id=607712990669832222&scope=bot&permissions=805694679>"


    async def com_pid (self, content, message):
        import os
        return f"PID: `{os.getpid ()}`"

    async def com_settings_set (self, args: list, message: discord.Message):
        if args[0] == kpoll_channel:
            if len (message.channel_mentions) != 1:
                return "Please also provide one mention to the new poll channel."
            self.configs[message.guild.id][kpoll_channel] = message.channel_mentions[0].id
            self.configs_save ()
            return f"Set {kpoll_channel} to {message.channel_mentions[0]}."

    async def com_settings_list (self, content: str, message: discord.Message):
        return "This feature is still a work-in-progress. Sorry!" # TODO

    async def com_settings (self, content: str, message: discord.Message):
        if message.guild is not None:
            if not message.author.guild_permissions.administrator:
                return f"{message.author.mention}, you must be administrator to use. Sorry!"
        else:
            return COMMAND_NOT_AVAIL_IN_DMS
        
        subcommands = {
            "set": self.com_settings_set,
            "list": self.com_settings_list, 
        }
        
        split = content
        args = ""
        if ' ' in content:
            split = content.split (" ")[0]
            args = content.split (" ")[1:]
        
        for _s, _fn in subcommands.items ():
            if split == _s:
                return await _fn (args, message)
        # if we get to here, no subcommand could be identified, so we just display the help
        return "Whoops, invalid arguments!\n\n" + (await self.com_help ("settings", message))

    commands = {
        "capify":     com_capify,
        "aA":         com_capify,
        "Aa":         com_capify,
        "spoilerize": com_spoilerize,
        "|":          com_spoilerize,
        "prefix":     com_prefix, # admin only
        "pda-prefix": com_prefix, # admin only
        "help":       com_help,
        "?":          com_help,
        "thanks":     com_thanks,
        "coinflip":   com_coinflip,
        "rng":        com_rng,
        "font":       com_font,
        "vote":       com_vote, # admin only, no help (yet)
        "poll":       com_poll,
        "calc":       com_calculate,
        "calculate":  com_calculate,
        "c":          com_calculate,
        "hello":      com_hello,
        "praise":     com_praise,
        "invite" :    com_invite,
        "pid" :       com_pid, # dev only, no help. returns current pid.
        "enable" :    com_enable, # admin only
        "disable":    com_disable, # admin only
        "settings" :  com_settings, # admin only
    }

    async def on_ready (self):
        log ('Logged on as {0} in guilds: {1}'.format (self.user,
                                                       self.guilds_list_str (
                                                           self.guilds)))
        self.configs_load ()
        for guild in self.guilds:
            if guild.id not in self.configs.keys ():
                log (
                    "[?] No config for \"" + guild.name + "\" found - creating "
                                                          "config")
                self.configs[guild.id] = self.default_config
            else:
                log (
                    "[OK] Config for \"" + guild.name + "\" found - prefix \"" +
                    self.configs[guild.id][kprefix] + "\"")
        self.configs_save ()

    async def on_message (self, message):
        log ('{0.guild}: Message from {0.author} in {0.channel}: \"{0.content}\"'.format (message))
        prefix = self.get_prefix (message)
        for (_c, _fn) in self.commands.items ():
            if message.content.startswith (prefix):
                magic_str = prefix + _c + " "
                if message.content.startswith (magic_str):
                    cont = ""
                    if message.guild is not None and _c in self.configs[message.guild.id][kdisabled_commands]:
                        cont = f"This command has been disabled. An admin can enable it with `{prefix}enable {_c}`."
                    else:
                        cont = await _fn (self, message.content[len (magic_str):], message)
                    await message.channel.send (content = cont)
                    break
                elif message.content == prefix + _c:
                    cont = ""
                    if message.guild is not None and _c in self.configs[message.guild.id][kdisabled_commands]:
                            cont = f"This command has been disabled. An admin can enable it with `{prefix}enable {_c}`."
                    else:
                        cont = await _fn (self, message.content[len (prefix + _c):],
                                        message)
                    await message.channel.send (content = cont)
                    break

        if message.content.startswith ("++pda_reset_prefix"):
            if message.guild is None:
                await message.channel.send (
                    content = "Cannot reset prefix for DMs.")
            else:
                if not message.author.guild_permissions.administrator:
                    await message.channel.send (
                        content = "Must be administrator to use. Sorry!")
                else:
                    self.configs[message.guild.id][kprefix] = self.default_prefix
                    await message.channel.send (
                        content = "Prefix reset to " + self.default_prefix)

        if message.author == self.user:
            log ('Message from [this bot]: \"{0.content}\"'.format (message))
        self.configs_save ()
        self.configs_load () # FIXME this is not the best way, but it fixes joining and not having any defaults configured

    async def on_message_delete (self, message: discord.Message):
        log ("Message by {0.author.id} ({0.author}) deleted: \"{0.content}\"".format (message))

    async def on_message_edit (self, before: discord.Message, after: discord.Message):
        log ("Message by {1.author.id} ({1.author}) edited:\nbefore:\n\"{0.content}" \
             "\"\nafter:\n\"{1.content}\"".format (before, after))

    async def on_connect (self):
        log ("Connected")

    async def on_disconnect (self):
        log ("Disconnected")
        await self.close ()

    async def on_resumed (self):
        log ("Resumed")

    async def on_member_join (self, member: discord.Member):
        log ("Member" + str (member.id) + "(" + str (
            member.display_name) + ") joined")

    async def on_member_remove (self, member: discord.Member):
        log ("Member" + str (member.id) + "(" + str (
            member.display_name) + ") left")

""" 
    async def on_member_update (self, before: discord.Member,
                                after: discord.Member):
        log ("Member update: " + str (after) + "\n\t" + str (
            before.status) + "\n\t" + str (
            before.activity) + "\n\t" + str (before.nick) + "\n\t" + str (
            len (before.roles)) +
             "\nNow:\n\t" + str (after.status) + "\n\t" + str (
            after.activity) + "\n\t" + str (
            after.nick) + "\n\t" + str (len (after.roles)))

    async def on_user_update (self, before: discord.User, after: discord.User):
        log ("User update: " + str (after) + "\n\t" + str (
            before.name) + "\n\t" + str (
            before.discriminator) + "\nNow:\n\t" + str (
            after.name) + "\n\t" + str (after.discriminator))
"""

try:
    with open ("TOKEN", "r") as f:
        Bot ().run (f.readline ().strip ())
except Exception as e:
    log (f"~~~ EXCEPTION: {e}")
