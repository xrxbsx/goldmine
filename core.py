"""The brains of Dragon5232's experimental Discord bot.'"""
from __future__ import unicode_literals

import logging
import asyncio

import discord

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
from util.const import description
from util.proformatter import RichFormatter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
store.initialize()

if not discord.opus.is_loaded():
    # Windows: opus.dll (auto provided)
    # Linux: CWD/libopus.so
    # Mac: CWD/libopus.dylib
    try:
        discord.opus.load_opus('opus')
    except OSError:
        try:
            discord.opus.load_opus('libopus')
        except OSError:
            logger.getChild('client').warning('could not load libopus, voice will NOT be available.')

def runbot(loop, bot):
    """Start the bot and handle Ctrl-C."""
    try:
        try:
            loop.run_until_complete(bot.start(bot_token))
        except RuntimeError:
            pass
    except KeyboardInterrupt:
        logger.info('The bot is now shutting down, please wait...')
        loop.run_until_complete(bot.logout())
        # cancel all tasks lingering

def main():
    """Executes the main bot."""
    bot = PBot(command_prefix='!', description=description, formatter=RichFormatter(), pm_help=None)
    bot.add_cog(Voice(bot))
    bot.add_cog(Roleplay(bot))
    bot.add_cog(Admin(bot))
    bot.add_cog(Luck(bot))
    bot.add_cog(Cosmetic(bot))
    bot.add_cog(Miscellaneous(bot))
    bot.add_cog(Utility(bot))
    loop = asyncio.get_event_loop()
    runbot(loop, bot)
    return bot.is_restart

if __name__ == '__main__':
    main()
