"""The brains of Dragon5232's awesome Discord bot.'"""
from __future__ import unicode_literals
import logging
import asyncio
import os
from fnmatch import filter
import discord
from token_loader import bot_token
from convert_to_old_syntax import rc_files, cur_dir
from util.probot import ProBot as PBot
from util.datastore import initialize as init_store
from util.const import description, non_essential_cogs
from util.proformatter import RichFormatter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')
try:
    handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='r+')
except FileNotFoundError:
    handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w+')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
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
            logger.warning('could not load libopus, voice will NOT be available.')

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
    logger.info('Init: Getting cog folder')
    cogs_dir = os.path.join(cur_dir, 'cogs')
    bot = PBot(command_prefix='!', description=description, formatter=RichFormatter(), pm_help=None)
    logger.info('Init: Searching for cogs')
    cogs = [i.replace('.py', '').replace(cogs_dir + os.path.sep, '') for i in filter(rc_files(cogs_dir), '*.py')]
    logger.info('Init: Cleaning up list')
    cogs.remove('__init__')
    cogs.remove('cog')
    for cog in non_essential_cogs:
        cogs.remove(cog)
    logger.info('Init: Loading cogs')
    for cog in cogs:
        logger.info('Init: Loading cog: ' + cog)
        bot.load_extension('cogs.' + cog)
    logger.info('Init: Loading extra cogs')
    try:
        with open('cogs.txt', 'r+') as f:
            for cog in [i.replace('\r', '').replace('\n', '') for i in f.readlines()]:
                try:
                    logger.info('Init: Loading extra cog: ' + cog)
                    bot.load_extension('cogs.' + cog)
                except ImportError:
                    logger.error('Could not load extra cog %s!' % cog)
                    exit(1)
    except FileNotFoundError:
        pass
    logger.info('Init: Initializing event loop')
    loop = asyncio.get_event_loop()
    logger.info('Init: Starting bot!')
    runbot(loop, bot)
    return bot.is_restart

if __name__ == '__main__':
    use_uvloop = False
    logger.info('Init: Detecting uvloop...')
    try:
        import uvloop
    except ImportError:
        logger.info('Init: Could not load uvloop')
    else:
        logger.info('Init: Will use uvloop.')
        use_uvloop = True
    main(use_uvloop)
