"""Definition of the bot's barebones cog class."""
import asyncio

class Cog:
    """Base cog module. To be used as a template."""
    def __init__(self, bot, cmdfix, bname):
        self.bot = bot
        self.loop = asyncio.get_event_loop()
        self.cmdfix = cmdfix
        self.bname = bname
