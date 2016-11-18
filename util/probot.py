"""The bot's ProBot subclass module, to operate the whole bot."""
from sys import exc_info
from discord.ext.commands import Bot
from cleverbot import Cleverbot

class ProBot(Bot):
    """The brain of the bot, ProBot."""

    def __init__(self, **kwargs):
        self.cb = Cleverbot()
        super().__init__(**kwargs)
    async def on_error(self, ev, *args, **kwargs):
        await self.say(str(exc_info()))
'''
    async def on_message(self, msg):
        """Handler for new messages sent."""
        try:
            myself = msg.server.me
        except AttributeError:
            myself = self.user
        if myself in msg.mentions:
            await self.send_message(msg.channel, msg.author.mention + ' ' + self.cb.ask(msg.content.strip(msg.server.me.mention)))
        super().on_message(msg)
'''