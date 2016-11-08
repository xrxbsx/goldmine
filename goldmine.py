from __future__ import unicode_literals

import logging
import random
import subprocess

import discord
from discord.ext import commands

from btoken import bot_token
from modules.voice import Voice
from modules.roleplay import Roleplay

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

def is_me(m):
    """Checks if author of a message is this bot."""
    return m.author == bot.user

description = '''Dragon5232's loyal bot written in Python, Goldmine.
Typically cool. Try not to expose the bugs! :P
Enjoy.
'''
logging.basicConfig(level=logging.INFO)
bot = commands.Bot(command_prefix=".", description=description)
bot.add_cog(Voice(bot))
bot.add_cog(Roleplay(bot))
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
    server = member.server
    fmt = 'Welcome {0.mention} to {1.name}!'
    await bot.send_message(server, fmt.format(member, server))

@bot.command()
async def calc(left: int, right: int):
    """Evaluates a mathematical experssion."""
    await bot.say(left + right)

@bot.command()
async def roll(dice: str):
    """Rolls a virtual dice in [# of rolls]d[Range: 1-N] format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await bot.say('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await bot.say(result)

@bot.command(description='Do you see this?')
async def choose(*choices: str):
    """Chooses between multiple choices."""
    await bot.say(random.choice(choices))

@bot.command()
async def lmgtfy(*args):
    """Generates a Let Me Google That For You link."""
    await bot.say('http://lmgtfy.com/?q=' + '+'.join(args))

@bot.command()
async def purge(channel: discord.Channel):
    """Removes all of this bot's messages on a channel."""
    deleted = await bot.purge_from(channel, limit=200, check=is_me)
    await bot.send_message(channel, 'Deleted {} message(s)'.format(len(deleted)))

@bot.command()
async def nuke(channel: discord.Channel):
    """NUKES a channel by deleting all messages!"""
    deleted = await bot.purge_from(channel, limit=1000)
    await bot.send_message(channel, 'Deleted {} message(s)'.format(len(deleted)))

def main():
    """Executes the main bot."""
    bot.run(bot_token)

if __name__ == '__main__':
    main()
