"""The bot's ProBot subclass module, to operate the whole bot."""
import asyncio
import discord
import discord.ext.commands as commands
from discord.ext.commands.bot import Context, StringView, CommandError, CommandNotFound
from cleverbot import Cleverbot
from properties import bot_name as bname
from util.perms import CommandPermissionError
from util.datastore import get_cmdfix, get_prop

class ProBot(commands.Bot):
    """The brain of the bot, ProBot."""

    auto_convo_starters = [
        'do',
        'oh',
        'are',
        'you',
        'u',
        'ur',
        'ready',
        'begin',
        'lets',
        'go',
        'p',
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
        'wut',
        'shut',
        'watch',
        'behave',
        'test',
        'testing',
        'stop',
        'stahp',
        'ask',
        'ho',
        'um',
        'uh',
        'y',
        'tell',
        'gre'
    ]

    def __init__(self, **kwargs):
        self.cb = Cleverbot()
        super().__init__(**kwargs)
        self.is_restart = False
        self.loop = asyncio.get_event_loop()

    async def sctx(self, ctx, msg):
        """Send a message to the context's message origin.'"""
        self.send_message(ctx.message.channel, msg)

    async def askcb(self, query):
        """A method of querying Cleverbot safe for async."""
        blocking_cb = self.loop.run_in_executor(None, self.cb.ask, query)
        return await blocking_cb

    async def on_command_error(self, exp, ctx):
        cmdfix = await get_cmdfix(ctx.message)
        cnf_fmt = '{0.mention} The command you tried to execute, `{2}{1}`, does not exist. Type `{2}help` for help.'
        npm_fmt = '{0.mention} Sorry, the `{2}{1}` command does not work in DMs. Try a channel.'
        ccd_fmt = '{0.mention} Sorry, the `{2}{1}` command is currently disabled. Try again later!'
        cpe_fmt = '{0.mention} Sorry, you don\'t have **permission** to execute `{2}{1}`!'
        cproc = ctx.message.content.split(' ')[0]
        cprocessed = cproc[len(cmdfix):]
        print(type(exp))
        if isinstance(exp, commands.CommandNotFound):
            await self.send_message(ctx.message.channel, cnf_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.NoPrivateMessage):
            await self.send_message(ctx.message.channel, npm_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.DisabledCommand):
            await self.send_message(ctx.message.channel, ccd_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.CommandInvokeError):
            if str(exp).startswith('Command raised an exception: CommandPermissionError: '):
                await self.send_message(ctx.message.channel, cpe_fmt.format(ctx.message.author, cprocessed, cmdfix))
            else:
                await self.send_message(ctx.message.channel, 'An internal error has occured!```' + str(exp) + '```')
        else:
            await self.send_message(ctx.message.channel, 'An internal error has occured!```' + str(exp) + '```')
            print('Warning: ' + str(exp))

    async def casein(self, substr, clist):
        """Return if a substring is found in any of clist."""
        for i in clist:
            if substr in i:
                return True
        return False

    def bdel(self, s, r): return s[len(r):]

    async def auto_cb_convo(self, msg, kickstart):
        """The auto conversation manager."""
        await self.send_typing(msg.channel)
        lmsg = msg.content.lower()
        reply = lmsg
        reply_bot = await self.askcb(self.bdel(lmsg, kickstart + ' '))
        await self.send_message(msg.channel, msg.author.mention + ' ' + reply_bot)
        while await self.casein('?', [reply_bot, reply]):
            rep = await self.wait_for_message(author=msg.author)
            reply = rep.content
            reply_bot = await self.askcb(reply)
            await self.send_message(msg.channel, msg.author.mention + ' ' + reply_bot)

    async def on_message(self, msg):
        cmdfix = await get_cmdfix(msg)
        try:
            myself = msg.server.me
        except AttributeError:
            myself = self.user
        if msg.author.id != myself.id:
            if not msg.author.bot:
                if not msg.channel.is_private:
                    int_name = await get_prop(msg, 'bot_name')
                    if msg.server.me.display_name != int_name:
                        await self.change_nickname(msg.server.me, int_name)
                if myself in msg.mentions:
                    await self.auto_cb_convo(msg, self.user.mention)
                elif msg.channel.is_private:
                    if msg.content.startswith(cmdfix):
                        await self.send_typing(msg.channel)
                        await self.process_commands(msg)
                    else:
                        await self.send_typing(msg.channel)
                        cb_reply = await self.askcb(msg.content)
                        await self.send_message(msg.channel, ':speech_balloon: ' + cb_reply)
                elif msg.content.lower().startswith(bname.lower() + ' '):
                    nmsg = self.bdel(msg.content.lower(), bname.lower())
                    for i in self.auto_convo_starters:
                        if nmsg.startswith(' ' + i):
                            await self.auto_cb_convo(msg, bname.lower() + ' ')
                        elif nmsg.endswith('?'):
                            await self.auto_cb_convo(msg, bname.lower() + ' ')
                        elif nmsg.startswith(', '):
                            await self.auto_cb_convo(msg, bname.lower() + ', ')
                        elif nmsg.startswith('... '):
                            await self.auto_cb_convo(msg, bname.lower() + '... ')
                else:
                    if msg.content.startswith(cmdfix):
                        await self.send_typing(msg.channel)
                        await self.process_commands(msg)

    async def process_commands(self, message):
        """|coro|
        This function processes the commands that have been registered
        to the bot and other groups. Without this coroutine, none of the
        commands will be triggered.
        By default, this coroutine is called inside the :func:`on_message`
        event. If you choose to override the :func:`on_message` event, then
        you should invoke this coroutine as well.
        Warning
        --------
        This function is necessary for :meth:`say`, :meth:`whisper`,
        :meth:`type`, :meth:`reply`, and :meth:`upload` to work due to the
        way they are written. It is also required for the :func:`on_command`
        and :func:`on_command_completion` events.
        Parameters
        -----------
        message : discord.Message
            The message to process commands for.
        """
        _internal_channel = message.channel
        _internal_author = message.author

        view = StringView(message.content)
        if self._skip_check(message.author, self.user):
            return

        prefix = await self._get_prefix(message)
        invoked_prefix = prefix

        if not isinstance(prefix, (tuple, list)):
            if not view.skip_string(prefix):
                return
        else:
            invoked_prefix = discord.utils.find(view.skip_string, prefix)
            if invoked_prefix is None:
                return

        # invoker = command name
        invoker = view.get_word()
        tmp = {
            'bot': self,
            'invoked_with': invoker,
            'message': message,
            'view': view,
            'prefix': invoked_prefix
        }
        ctx = Context(**tmp)
        del tmp

        if invoker in self.commands:
            command = self.commands[invoker]
            self.dispatch('command', command, ctx)
            try:
                await command.invoke(ctx)
            except CommandError as e:
                ctx.command.dispatch_error(e, ctx)
            else:
                self.dispatch('command_completion', command, ctx)
        elif invoker:
            exc = CommandNotFound('Command "{}" is not found'.format(invoker))
            self.dispatch('command_error', exc, ctx)
