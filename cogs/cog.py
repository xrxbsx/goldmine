"""Definition of the bot's barebones cog class."""
import asyncio
import logging

class Cog:
    """Base cog module. To be used as a template."""
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('discord').getChild('client')
        self.loop = asyncio.get_event_loop()
        self.store = self.bot.store
        self.dstore = self.store.store
