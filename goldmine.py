from __future__ import unicode_literals

import logging
import random
import subprocess

import discord
from discord.ext import commands

from btoken import bot_token
from modules.voice import Voice
from modules.roleplay import Roleplay
from modules.admin import Admin
from modules.luck import Luck

if not discord.opus.is_loaded():
    # the 'opus' library here is opus.dll on windows
    # or libopus.so on linux in the current directory
    # you should replace this with the location the
    # opus library is located in and with the proper filename.
    # note that on windows this DLL is automatically provided for you
    try:
        discord.opus.load_opus('opus')
    except OSError:
        discord.opus.load_opus('libopus')

def is_me(mem):
    """Checks if author of a message is this bot."""
    return mem.author == bot.user

description = '''Dragon5232's loyal bot written in Python, Goldmine.
Typically cool. Try not to expose the bugs! :P
Enjoy.
'''
logging.basicConfig(level=logging.INFO)
bot = commands.Bot(command_prefix="!", description=description)
bot.add_cog(Voice(bot))
bot.add_cog(Roleplay(bot))
bot.add_cog(Admin(bot))
bot.add_cog(Luck(bot))
cvoice = None

@bot.event
async def on_ready():
    """On_ready event for when the bot logs into Discord."""
    print('Goldmine has logged into Discord as')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('-----------------------------------')

@bot.event
async def on_member_join(member: discord.Member):
    """On_member_join event for newly joined members."""
    cemotes = [i.name for i in member.server.emojis]
    fmt = '''Welcome {0.mention} to **{1.name}**. Have a good time here! :wink:
If you need any help, contact an admin, moderator, or helper with your :question::question:s.
Remember to use the custom emotes: {2} for extra fun!
'''
    await bot.send_message(member.server, fmt.format(member, member.server,
                                                     ' '.join([':'+i+':' for i in cemotes])))

@bot.command()
async def calc(left: int, right: int):
    """Evaluates a mathematical experssion."""
    await bot.say(left + right)

@bot.command()
async def lmgtfy(*args):
    """Generates a Let Me Google That For You link."""
    await bot.say('http://lmgtfy.com/?q=' + '+'.join(args))

@bot.command(pass_context=True)
async def emotes(ctx):
    """Lists all the current custom emoji on this server."""
    await bot.say(' '.join([':'+i.name+':' for i in ctx.message.author.server.emojis]))

def main():
    """Executes the main bot."""
    bot.run(bot_token)

if __name__ == '__main__':
    main()
