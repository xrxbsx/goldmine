"""The brains of Dragon5232's awesome Discord bot.'"""
from __future__ import unicode_literals
import logging
import asyncio
import os
from fnmatch import filter
import discord
from btoken import bot_token
from convert_to_old_syntax import rc_files, cur_dir
from util.probot import ProBot as PBot
from util.datastore import initialize as init_store
from util.const import description
from util.proformatter import RichFormatter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
init_store()

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

def main(use_uvloop):
    """Executes the main bot."""
    if use_uvloop:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    print(' - Getting cog folder')
    cogs_dir = os.path.join(cur_dir, 'cogs')
    bot = PBot(command_prefix='!', description=description, formatter=RichFormatter(), pm_help=None)
    print(' - Searching for cogs')
    cogs = [i.replace('.py', '').replace(cogs_dir + os.path.sep, '') for i in filter(rc_files(cogs_dir), '*.py')]
    print(' - Cleaning up list')
    cogs.remove('__init__')
    cogs.remove('cog')
    print(' - Loading cogs')
    for cog in cogs:
        print(' - Loading cog: ' + cog)
        bot.load_extension('cogs.' + cog)
    print(' - Initializing event loop')
    loop = asyncio.get_event_loop()
    print(' - Starting bot!')
    runbot(loop, bot)
    return bot.is_restart

if __name__ == '__main__':
    use_uvloop = False
    print(' - Detecting uvloop...')
    try:
        import uvloop
    except ImportError:
        print(' - Could not load uvloop')
        pass
    else:
        print(' - Will use uvloop.')
        use_uvloop = True
    main(use_uvloop)
