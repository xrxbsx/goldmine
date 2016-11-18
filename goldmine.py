"""Goldmine, Dragon5232's experimental Discord bot.'"""
from __future__ import unicode_literals

import logging
import asyncio

import discord
from discord.ext import commands
from cleverbot import Cleverbot

from btoken import bot_token
from bot_name import bname
from modules.voice import Voice
from modules.roleplay import Roleplay
from modules.admin import Admin
from modules.luck import Luck
from modules.cosmetic import Cosmetic
from util.safe_math import eval_expr as emath
from util.probot import ProBot as PBot

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

cmdfix = '!'
description = '''Dragon5232's loyal bot written in Python, ''' + bname + '''.
Typically cool. Try not to expose the bugs! :P
Enjoy, and leave comments for Dragon5232!
Note: to find out how to use a command, type ''' + cmdfix + '''help [command name].'''
cb = Cleverbot()

logging.basicConfig(level=logging.INFO)
bot = PBot(command_prefix=commands.when_mentioned_or(cmdfix), description=description)
bot.add_cog(Voice(bot, cmdfix))
bot.add_cog(Roleplay(bot, cmdfix))
bot.add_cog(Admin(bot, cmdfix))
bot.add_cog(Luck(bot, cmdfix))
bot.add_cog(Cosmetic(bot, cmdfix))
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
Remember to use the custom emotes: {2} for extra fun! You can access my help with {3}help.
'''
    await bot.send_message(member.server, fmt.format(member, member.server,
                                                     ' '.join([':'+i+':' for i in cemotes]), cmdfix))

@bot.event
async def on_member_remove(member: discord.Member):
    """On_member_remove event for members leaving."""
    fmt = '''Awww, **{0.mention}** has just left this server. Bye bye, **{0.mention}**!
**{1.name}** has now lost a {2}. I wonder why..?
The more members, the more fun, especially when they're friends like this one! :bear:
'''
    await bot.send_message(member.server, fmt.format(member, member.server, 'member'))

@bot.command()
async def calc(*args):
    """Evaluates a mathematical experssion.
    Syntax: calc [expression]"""
    await bot.say(emath(' '.join(args)))

@bot.command()
async def lmgtfy(*args):
    """Generates a Let Me Google That For You link.
    Syntax: lmgtfy [search terms]"""
    await bot.say('http://lmgtfy.com/?q=' + '+'.join(args))

@bot.command(pass_context=True)
async def emotes(ctx):
    """Lists all the current custom emoji on this server.
    Syntax: emotes"""
    await bot.say(' '.join([':'+i.name+':' for i in ctx.message.author.server.emojis]))

def main():
    """Executes the main bot."""

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(bot.start(bot_token))
    except KeyboardInterrupt:
        loop.run_until_complete(bot.logout())
        # cancel all tasks lingering
    finally:
        loop.close()

if __name__ == '__main__':
    main()
