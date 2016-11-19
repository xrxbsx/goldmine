"""The bot's ProBot subclass module, to operate the whole bot."""
from sys import exc_info
from discord.ext.commands import Bot
from cleverbot import Cleverbot
import asyncio

class ProBot(Bot):
    """The brain of the bot, ProBot."""

    def __init__(self, **kwargs):
        self.cb = Cleverbot()
        super().__init__(**kwargs)
        self.is_restart = False
        self.loop = asyncio.get_event_loop()

    async def on_error(self, ev, *args, **kwargs):
        await self.say('_EXLOG: handled ' + str(exc_info()))