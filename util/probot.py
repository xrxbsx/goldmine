"""The bot's ProBot subclass module, to operate the whole bot."""
import asyncio
import sys
import traceback
from discord.ext.commands import Bot
from cleverbot import Cleverbot

class ProBot(Bot):
    """The brain of the bot, ProBot."""

    def __init__(self, **kwargs):
        self.cb = Cleverbot()
        super().__init__(**kwargs)
        self.is_restart = False
        self.loop = asyncio.get_event_loop()

    async def on_command_error(self, exp, ctx):
        print('Warning: caught exception in command {}'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(exp), exp, exp.__traceback__, file=sys.stderr)
