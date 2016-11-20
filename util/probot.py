"""The bot's ProBot subclass module, to operate the whole bot."""
import asyncio
import discord.ext.commands as commands
from cleverbot import Cleverbot
from properties import command_prefix as cmdfix
from properties import bot_name as bname
from util.perms import CommandPermissionError

class ProBot(commands.Bot):
    """The brain of the bot, ProBot."""

    auto_convo_starters = [
        'do',
        'oh',
        'are',
        'you',
        'u',
        'ur',
        'youre',
        'your',
        'you\'re',
        'you are',
        'ready',
        'begin',
        'lets',
        'go',
        'pls',
        'plz',
        'plez',
        'please',
        'can',
        'could',
        'would',
        'will',
        'hi',
        'hello',
        'hey',
        'heya',
        'hoi',
        'what',
        'wot',
        'wut'
    ]

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
        ccd_fmt = '{0.mention} Sorry, the `{2}{1}` command is currently disabled. Try again later!'
        cpe_fmt = '{0.mention} Sorry, you don\'t have **permission** to execute `{2}{1}`!'
        cproc = ctx.message.content.split(' ')[0]
        cprocessed = cproc[len(cmdfix):]
        if isinstance(exp, commands.CommandNotFound):
            await self.send_message(ctx.message.channel, cnf_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.NoPrivateMessage):
            await self.send_message(ctx.message.channel, npm_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.DisabledCommand):
            await self.send_message(ctx.message.channel, ccd_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, CommandPermissionError):
            await self.send_message(ctx.message.channel, cpe_fmt.format(ctx.message.author, cprocessed, cmdfix))
        else:
            await self.send_message(ctx.message.channel, 'An internal error has occured!```' + str(exp) + '```')
            print(str(exp))

    async def auto_cb_convo(self, msg, kickstart):
        lmsg = msg.content.lower()
        reply_bot = self.cb.ask(lmsg.strip(kickstart + ' '))
        await self.send_message(msg.channel, msg.author.mention + ' ' + reply_bot)
        while '?' in reply_bot:
            reply = await self.wait_for_message(author=msg.author)
            reply_bot = self.cb.ask(reply)
            await self.send_message(msg.channel, msg.author.mention + ' ' + reply_bot)

    async def on_message(self, msg):
        try:
            myself = msg.server.me
        except AttributeError:
            myself = self.user
        if myself in msg.mentions:
            await self.auto_cb_convo(msg, self.bot.user.mention)
        elif msg.content.lower().startswith(bname.lower() + ' '):
            nmsg = msg.content.lower().strip(bname.lower() + ' ')
            for i in self.auto_convo_starters:
                if nmsg.startswith(i + ' '):
                    await self.auto_cb_convo(msg, bname.lower() + ' ')
                elif nmsg.endswith('?'):
                    await self.auto_cb_convo(msg, bname.lower() + ' ')
        else:
            await self.process_commands(msg)
