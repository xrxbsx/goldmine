"""The brains of Dragon5232's experimental Discord bot.'"""
from __future__ import unicode_literals

import logging
import asyncio

import discord
from cleverbot import Cleverbot

from btoken import bot_token
from modules.voice import Voice
from modules.roleplay import Roleplay
from modules.admin import Admin
from modules.luck import Luck
from modules.cosmetic import Cosmetic
from modules.misc import Misc as Miscellaneous
from modules.utility import Utility
from util.probot import ProBot as PBot
import util.datastore as store
from util.const import description, bool_true
from util.proformatter import ProFormatter

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

cb = Cleverbot()

logging.basicConfig(level=logging.INFO)
store.initialize()
bot = PBot(command_prefix='!', description=description, formatter=ProFormatter(), pm_help=True)
bot.add_cog(Voice(bot))
bot.add_cog(Roleplay(bot))
bot.add_cog(Admin(bot))
bot.add_cog(Luck(bot))
bot.add_cog(Cosmetic(bot))
bot.add_cog(Miscellaneous(bot))
bot.add_cog(Utility(bot))
cvoice = None
restart = False

@bot.event
async def on_member_join(member: discord.Member):
    """On_member_join event for newly joined members."""
    cemotes = member.server.emojis
    em_string = (': ' + ' '.join([str(i) for i in cemotes]) if len(cemotes) >= 1 else '')
    fmt = '''Welcome {0.mention} to **{1.name}**. Have a good time here! :wink:
If you need any help, contact someone with your :question::question:s.
Remember to use the custom emotes{2} for extra fun! You can access my help with {3}help.
'''
    if store.get_prop(member, 'broadcast_join') in bool_true:
        await bot.send_message(member.server, fmt.format(member, member.server,
                                                         em_string))

@bot.event
async def on_member_remove(member: discord.Member):
    """On_member_remove event for members leaving."""
    fmt = '''Awww, **{0.mention}** has just left this server. Bye bye, **{0.mention}**!
**{1.name}** has now lost a {2}. We'll miss you! :bear:
'''
    if store.get_prop(member, 'broadcast_leave') in bool_true:
        utype = ('bot' if member.bot else 'member')
        await bot.send_message(member.server, fmt.format(member, member.server, utype))

def runbot(loop):
    """Start the bot and handle Ctrl-C."""
    try:
        try:
            loop.run_until_complete(bot.start(bot_token))
        except RuntimeError:
            pass
    except KeyboardInterrupt:
        print('The bot is now shutting down, please wait...')
        loop.run_until_complete(bot.logout())
        # cancel all tasks lingering

def main():
    """Executes the main bot."""
    loop = asyncio.get_event_loop()
    runbot(loop)
    return bot.is_restart

if __name__ == '__main__':
    main()
