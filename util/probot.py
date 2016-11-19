"""The bot's ProBot subclass module, to operate the whole bot."""
import asyncio
import discord.ext.commands as commands
from cleverbot import Cleverbot
from properties import command_prefix as cmdfix

class ProBot(commands.Bot):
    """The brain of the bot, ProBot."""

    def __init__(self, **kwargs):
        self.cb = Cleverbot()
        super().__init__(**kwargs)
        self.is_restart = False
        self.loop = asyncio.get_event_loop()

    async def sctx(self, ctx, msg):
        """Send a message to the context's message origin.'"""
        self.send_message(ctx.message.channel, msg)

    async def on_command_error(self, exp, ctx):
        cnf_fmt = '{0.mention} The command you tried to execute, `{2}{1}`, does not exist. Type `{2}help` for help.'
        npm_fmt = '{0.mention} Sorry, the `{2}{1}` command does not work in DMs. Try a full channel.'
        cprocessed = ctx.message.content.split(' ')[0][len(cmdfix):]
        if isinstance(exp, commands.CommandNotFound):
            await self.send_message(ctx.message.channel, cnf_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.NoPrivateMessage):
            await self.send_message(ctx.message.channel, npm_fmt.format(ctx.message.author, cprocessed, cmdfix))
        else:
            await self.send_message(ctx.message.channel, 'An internal error has occured!```' + str(exp) + '```')
            print(str(exp))

