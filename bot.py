# Author @lionkor on github.com
#
# I know this code is really bad, I'll refactor it later.
# It's just a hobby project, you should not use this for
# bigger servers, probably.
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
import sys
import calc # my own calculator module

class Config:
    prefix = "+"
    polls_enabled = False
    poll_channel = -1


def time_str ():
    dtn = datetime.now ()
    return str (dtn.date ()) + " " + str (dtn.hour) + ":" + str (
        dtn.minute) + ":" + str (dtn.second)


def log (msg):
    time = time_str ()
    # print (time + " [LOG] " + str (msg))
    print (time + " [LOG] " + str (msg), file = open ("log.txt", "a"))

class Bot (discord.Client):
    configs: {discord.Guild.id, Config} = dict ()

    votes = dict ()  # {message_id: [upvotes, downvotes], }

    async def capify (self, msg: str, message: discord.Message):
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
        # deleting the message (feature requested by users)
        await message.delete ()
        return "{0}: {1}".format (message.author.display_name, result)

    async def spoilerize (self, msg: str, message: discord.Message):
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

    def save_configs (self):
        f = open ("configs.data", "w+")
        for (_id, _conf) in self.configs.items ():
            f.write (str (_id) + ":" + str (_conf.prefix) + "," + str (
                _conf.polls_enabled) + "," + str (
                _conf.poll_channel) + ",\n")
        f.close ()

    def load_configs (self):
        # {discord.Guild.id, Config}
        f = open ("configs.data", "r")
        for _line in f:
            line = _line.strip ()
            if line == "":
                continue
            _id = int (line.split (':')[0])
            self.configs[_id] = Config ()
            self.configs[_id].prefix = line.split (':')[1].split (',')[0]
            self.configs[_id].polls_enabled = bool (
                line.split (':')[1].split (',')[1])
            self.configs[_id].poll_channel = int (
                line.split (':')[1].split (',')[2])
        f.close ()

    async def set_prefix (self, msg: str, message: discord.Message):
        if message.guild is None:
            return "Setting the prefix in DMs is not yet supported."
        else:
            if not message.author.guild_permissions.administrator:
                return "Must be administrator to use. Sorry!"
            self.configs[message.guild.id].prefix = msg
            return "Prefix set to `" + self.configs[
                message.guild.id].prefix + "`"

    async def display_help (self, msg: str, message: discord.Message):
        log ("help: " + msg)
        prefix = Config ().prefix
        if message.guild is not None:
            prefix = self.configs[message.guild.id].prefix
        if len (msg) > 0:
            for _command in self.command_help:
                for _item in _command[0]:
                    if msg == _item:
                        return "`" + prefix + _command[1].format (_item)
            return "command `{0}` not found.".format (msg)
        else:
            fullhelp = "\t\t**PDA Help**\n\n" \
                       "_To use the following commands, " \
                       "precede them with `{0}`._\n\n".format (prefix)
            for _command in self.command_help:
                for _item in _command[0]:
                    fullhelp += "`" + prefix + _command[1].format (_item) + "\n"
            return fullhelp

    async def thank (self, content, message: discord.Message):
        with open ("thanks.txt", "a") as f:
            f.write (time_str () + " " + str (message.author.id) + " (" + str (
                message.author) + ") thanked me!\n")
        return "Noted! I appreciate it :)"

    async def setup_vote (self, content: str, message: discord.Message):
        if message.guild is None:
            return "Must be in a server."
        else:
            if not message.author.guild_permissions.administrator:
                return "Must be administrator to use. Sorry!"
            # must mention a channel
            if len (message.channel_mentions) == 0:
                return "Must mention a channel, try again."
            # now message.channel_mentions[0] is the channel to send vote in
            msg: discord.Message = (await message.channel_mentions[0].send (
                content = content[content.find (" "):]))
            await msg.add_reaction (u"\U0001F53C")
            await msg.add_reaction (u"\U0001F53D")
            self.votes[msg.id] = [0, 0]

    async def coinflip (self, content: str, message: discord.Message):
        if random.randint (0, 1) == 0:
            return "Heads!"
        else:
            return "Tails!"

    async def rng (self, content: str, message: discord.Message):
        numbers = content.split (" ")
        if len (numbers) != 2:
            return "Incorrect number of arguments! I only need minimum and " \
                   "maximum!"
        try:
            _min = int (numbers[0])
            _max = int (numbers[1])
        except Exception as e:
            log (str (e))
            return "Make sure both arguments are _whole_ numbers!"
        return "RNG: " + str (
            random.randint (min (_min, _max), max (_min, _max)))

    async def font (self, content: str, message: discord.Message):
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
            return "I don't know that font! Do `help font` to learn more."
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


    async def praise (self, content: str, message: discord.Message):
        if len (message.mentions) == 0:
            return "Please metion someone that should be praised"
        _first : str  = random.choice (self.praises_first)  # main part of the message
        _second : str = random.choice (self.praises_second) # thing to compliment
        return _first.format (_second, message.mentions[0].mention)

    async def toggle_polls (self, content: str, message: discord.Message):
        if message.guild is not None:
            if not message.author.guild_permissions.administrator:
                return "Must be administrator to use. Sorry!"
            self.configs[message.guild.id].polls_enabled = bool (content)
            return "Polls toggled!"
        else:
            polls_enabled = Config ().polls_enabled
            return "Polls cannot be toggled in DMs."

    # TODO delete poll

    async def start_poll (self, content: str, message: discord.Message):
        content = content.replace ("@everyone", "@ everyone").replace ("@here",
                                                                       "@ here")
        if message.guild is None:
            return "Can't do polls in DMs."
        else:
            if not self.configs[message.guild.id].polls_enabled:
                return "Polls are disabled. Contact an admin."
            if self.configs[message.guild.id].poll_channel == -1:
                self.configs[message.guild.id].poll_channel = (
                    await message.guild.create_text_channel ("polls")).id
            channel: discord.TextChannel = message.guild.get_channel (
                self.configs[message.guild.id].poll_channel)
            msg: discord.Message = (
                await channel.send (content = content + " (by {0})".format (
                    message.author.mention)))
            await msg.add_reaction (u"\U0001F53C")
            await msg.add_reaction (u"\U0001F53D")
            await message.delete () # remove original message (requested by users)

    async def calculate (self, content: str, message: discord.Message):
        await message.channel.send (content=content + " = " + calc.calc (content))

    async def hello (self, content: str, message: discord.Message):
        prefix = Config ().prefix
        if message.guild is not None:
            prefix = self.configs[message.guild.id].prefix
        await message.channel.send (content="Hello, {0}! I am this server's **P**ersonal **D**igital **A**ssistant, PDA. You can get a list of commands by typing `{1}help`. My author is Lion#3620, so talk to him if you have any feature requests or problems, or use the poll below! \n\nMy code is here: <https://github.com/lionkor/discord_PDA>. \n\nHere's a short poll about me: <https://forms.gle/WeJ9JqDABEsAyVhL8>."
                .format (message.author.display_name, prefix))

    commands = {
        "capify": capify,
        "aA": capify,
        "Aa": capify,
        "spoilerize": spoilerize,
        "|": spoilerize,
        "prefix": set_prefix,  # admin only
        "help": display_help,
        "?": display_help,
        "thanks": thank,
        "coinflip": coinflip,
        "rng": rng,
        "font": font,
        "vote": setup_vote,  # admin only
        "polls": toggle_polls,  # admin only
        "poll": start_poll,
        "calc": calculate,
        "calculate": calculate,
        "c": calculate,
        "hello": hello,
        "praise": praise,
        # "lock_vote": lock_vote, # admin only
    }

    command_help = [
        [["capify", "aA", "Aa"],
         "{0} <text>` - cApItAlIzEs given text in a fun way."],
        [["spoilerize", "|"],
         "{0} <text>` - Surrounds each letter in the text with a spoiler "
         "(\"||h||||i||||!||\")."],
        [["help", "?"],
         "{0} [command]` - Displays this help or help about a specific "
         "command."],
        [["prefix"],
         "{0} <prefix>` - Changes the prefix serverwide. Does not work in "
         "DMs (yet). Can be reset with `++pda_reset_prefix`."],
        [["thanks"], "{0}` - Thank the bot for its hard work!"],
        [["coinflip"], "{0}` - Flips a coin (randomly gives Heads or Tails)."],
        [["rng"],
         "{0} <min> <max>` - Random number generator - returns a number "
         "between `min` and `max`!"],
        [["font"],
         "{0} <fontname> <text>` - Turns text into text of a different font! "
         "Avaliable fonts: nice, mono, super, circle, tiny, fraktur"],
        [["calculate", "calc", "c"], "{0} <expression>` - Attempts to calculate the given expression. Examples: `2 * 53`, `3444.343 / (32 + 2.2)`"],
        [["hello"], "{0}` - Displays some information about this bot."],
    ]

    async def on_ready (self):
        log ('Logged on as {0} in guilds: {1}'.format (self.user,
                                                       self.guilds_list_str (
                                                           self.guilds)))
        self.load_configs ()
        for guild in self.guilds:
            if guild.id not in self.configs:
                log (
                    "[?] No config for \"" + guild.name + "\" found - creating "
                                                          "config")
                self.configs[guild.id] = Config ()
            else:
                log (
                    "[OK] Config for \"" + guild.name + "\" found - prefix \"" +
                    self.configs[guild.id].prefix + "\"")
        self.save_configs ()

    async def on_message (self, message):
        log ('{0.guild}: Message from {0.author} in {0.channel.name}: \"{0.content}\"'.format (message))
        prefix = ""
        has_prefix = False
        if message.guild is not None:
            prefix = self.configs[message.guild.id].prefix
        else:
            prefix = Config ().prefix
        for (_c, _fn) in self.commands.items ():
            if message.content.startswith (prefix):
                has_prefix = True
                magic_str = prefix + _c + " "
                if message.content.startswith (magic_str):
                    await message.channel.send (
                        content = (
                            await _fn (self, message.content[len (magic_str):],
                                       message)))
                    break
                elif message.content.startswith (prefix + _c):
                    await message.channel.send (
                        content = (await _fn (self, message.content[
                                                    len (magic_str) - 1:],
                                              message)))
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
                    self.configs[message.guild.id].prefix = Config ().prefix
                    await message.channel.send (
                        content = "Prefix reset to " + Config ().prefix)

        if has_prefix:
            log (
                'Message from {0.author} in \"{0.channel}\": \"{0.content}\"'
                    .format (message))

        if message.author == self.user:
            log ('Message from [this bot]: \"{0.content}\"'.format (message))
        self.save_configs ()

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

while True:
    try:
        with open ("TOKEN", "r") as f:
            Bot ().run (f.readline ().strip ())
    except Exception as e:
        log ("~~~ EXCEPTION:", e)
