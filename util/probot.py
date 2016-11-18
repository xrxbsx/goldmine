"""The bot's ProBot subclass module, to operate the whole bot."""
from sys import exc_info
from discord.ext.commands import Bot

class ProBot(Bot):
    """The brain of the bot, ProBot."""
    async def on_error(self, ev, *args, **kwargs):
        await self.say(str(exc_info()))
