"""The bot's ProBot subclass module, to operate the whole bot."""
import asyncio
import discord
import discord.ext.commands as commands
from discord.ext.commands.bot import Context, StringView, CommandError, CommandNotFound
from cleverbot import Cleverbot
from util.datastore import get_cmdfix, get_prop, set_prop
import util.ranks as rank

class CleverQuery():
    def __init__(self, channel_to, query, prefix, suffix):
        self.destination = channel_to
        self.prefix = prefix
        self.suffix = suffix
        self.query = query

class ProBot(commands.Bot):
    """The brain of the bot, ProBot."""

    auto_convo_starters = [
        'do', 'oh',
        'are', 'you',
        'u', 'ur',
        'ready', 'begin',
        'lets',
        'go',
        'p',
        'c',
        'h',
        'w',
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
        'why',
        'd',
        'g'
    ]
    q_replies = [
        'What is the answer then.',
        'Why.',
        'Yes or no.',
        'You tell me.',
        'Erare humanum est.',
        'Hi.',
        'Hello.'
    ]
    cnf_fmt = '{0.mention} The command you tried to execute, `{2}{1}`, does not exist. Type `{2}help` for help.'
    npm_fmt = '{0.mention} Sorry, the `{2}{1}` command does not work in DMs. Try a channel.'
    ccd_fmt = '{0.mention} Sorry, the `{2}{1}` command is currently disabled. Try again later!'
    cpe_fmt = '{0.mention} Sorry, you don\'t have enough **permissions** to execute `{2}{1}`!'
    ece_fmt = '{0.mention} Hey, we don\'t have empty commands here! Try `{2}help` instead of `{2}` for help.'

    def __init__(self, **kwargs):
        self.cb = Cleverbot()
        self.is_restart = False
        self.loop = asyncio.get_event_loop()
        self.auto_convos = []
        self.game = {
            'name': 'Dragon Essence',
            'type': 1,
            'url': 'https://www.twitch.tv/dragon5232'
        }
        self.status = 'dnd'
        self.presence = {}
        self.main_cb_queue = asyncio.Queue() # For cleverbot
        self.alt_cb_queue = asyncio.Queue() # For cleverbutts
        self.main_cb_executor = self.loop.create_task(self.cb_task(self.main_cb_queue))
        self.alt_cb_executor = self.loop.create_task(self.cb_task(self.alt_cb_queue))
        super().__init__(**kwargs)

    @asyncio.coroutine
    def cb_task(self, queue):
        """Handle the answering of all Cleverbot queries."""
        while True:
            queue.clear()
            current = yield from queue.get()
            cb_args = [
                current.destination,
                current.query,
                current.prefix,
                current.suffix,
                queue
            ]
            yield from self.cb_ask(*cb_args)
            yield from queue.wait()

    @asyncio.coroutine
    def update_presence(self):
        """Generate an updated presence and change it."""
        self.presence = {
            'game': discord.Game(**self.game),
            'status': discord.Status(self.status)
        }
        yield from self.change_presence(**self.presence)

    @asyncio.coroutine
    def sctx(self, ctx, msg):
        """Send a message to the context's message origin.'"""
        self.send_message(ctx.message.channel, msg)

    @asyncio.coroutine
    def cb_ask(self, dest, query, prefix, suffix, queue):
        blocking_cb = self.loop.run_in_executor(None, self.cb.ask, query)
        reply_bot = yield from blocking_cb
        yield from self.send_message(dest, prefix + query + suffix)
        yield from asyncio.sleep(2)
        queue.set()
    @asyncio.coroutine
    def askcb(self, query):
        """A method of querying Cleverbot safe for async."""
        blocking_cb = self.loop.run_in_executor(None, self.cb.ask, query)
        tmp = yield from blocking_cb
        return tmp

    @asyncio.coroutine
    def on_command_error(self, exp, ctx):
        cmdfix = yield from get_cmdfix(ctx.message)
        cproc = ctx.message.content.split(' ')[0]
        cprocessed = cproc[len(cmdfix):]
        print(ctx.message.server.id + ': ' + str(type(exp)) + ' - ' + str(exp))
        if isinstance(exp, commands.CommandNotFound):
            yield from self.send_message(ctx.message.channel, self.cnf_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.NoPrivateMessage):
            yield from self.send_message(ctx.message.channel, self.npm_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.DisabledCommand):
            yield from self.send_message(ctx.message.channel, self.ccd_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.CommandInvokeError):
            if str(exp).startswith('Command raised an exception: CommandPermissionError: ' + cmdfix):
                yield from self.send_message(ctx.message.channel, self.cpe_fmt.format(ctx.message.author, cprocessed, cmdfix))
            else:
                yield from self.send_message(ctx.message.channel, 'An internal error has occured!```' + str(exp) + '```')
        else:
            yield from self.send_message(ctx.message.channel, 'An internal error has occured!```' + str(exp) + '```')

    def casein(self, substr, clist):
        """Return if a substring is found in any of clist."""
        for i in clist:
            if substr in i:
                return True
        return False

    @staticmethod
    def bdel(s, r): return s[len(r):]

    @asyncio.coroutine
    def auto_cb_convo(self, msg, kickstart):
        """The auto conversation manager."""
        if self.status == 'invisible': return
        absid = msg.server.id + ':' + msg.channel.id + ':' + msg.author.id
        if absid not in self.auto_convos:
            yield from self.send_typing(msg.channel)
            self.auto_convos.append(absid)
            lmsg = msg.content.lower()
            reply = lmsg
            reply_bot = yield from self.askcb(self.bdel(lmsg, kickstart + ' ')) #ORIG
            yield from self.send_message(msg.channel, msg.author.mention + ' ' + reply_bot) #ORIG
#            cb_query = CleverQuery(msg.channel, self.bdel(lmsg, kickstart + ' '), msg.author.mention + ' ', '') #NEW
#            yield from self.main_cb_queue.put(cb_query) #NEW
            while (self.casein('?', [reply_bot, reply])) or (reply_bot in self.q_replies):
                rep = yield from self.wait_for_message(author=msg.author)
                reply = rep.content
#                cb_query = CleverQuery(msg.channel, self.bdel(lmsg, kickstart + ' '), msg.author.mention + ' ', '') #NEW
#                yield from self.main_cb_queue.put(cb_query) #NEW
                reply_bot = yield from self.askcb(reply) #ORIG
                yield from self.send_message(msg.channel, msg.author.mention + ' ' + reply_bot) #ORIG
            self.auto_convos.remove(absid)

    @asyncio.coroutine
    def on_ready(self):
        """On_ready event for when the bot logs into Discord."""
        print('Bot has logged into Discord, ID ' + self.user.id)
        yield from self.update_presence()

    @asyncio.coroutine
    def on_message(self, msg):
        cmdfix = yield from get_cmdfix(msg)
        bname = yield from get_prop(msg, 'bot_name')
        try:
            myself = msg.server.me
        except AttributeError:
            myself = self.user
        if msg.author.id != myself.id:
            if str(msg.channel) == 'cleverbutts':
                if msg.content == 'cleverbutts kickstart main':
                    yield from self.send_message(msg.channel, 'Hi, how are you doing?')
                    return
            if msg.author.bot:
                if self.status == 'invisible': return
                if str(msg.channel) == 'cleverbutts':
                    yield from self.send_typing(msg.channel)
                    #yield from self.main_cb_queue.put(CleverQuery(msg.channel, msg.content, '', ''))
                    reply_bot = yield from self.askcb(msg.content)
                    yield from asyncio.sleep(2)
                    yield from self.send_message(msg.channel, reply_bot)
                    yield from asyncio.sleep(1)
            else:
                if not msg.channel.is_private:
                    int_name = yield from get_prop(msg, 'bot_name')
                    if msg.server.me.display_name != int_name:
                        yield from self.change_nickname(msg.server.me, int_name)
                    if not msg.content.startswith(cmdfix):
                        prof_name = 'profile_' + msg.server.id
                        prof = yield from get_prop(msg, prof_name)
                        prof['exp'] += 2
                        new_level = rank.xp_level(prof['exp'])[0]
                        if new_level > prof['level']:
                            yield from self.send_message(msg.channel, '**Hooray!** {0.mention} has just *advanced to* **level {1}**! Nice! Gotta get to **level {2}** now! :stuck_out_tongue:'.format(msg.author, str(new_level), str(new_level + 1)))
                        prof['level'] = new_level
                        yield from set_prop(msg, 'by_user', prof_name, prof)
                if self.status == 'invisible':
                    if msg.content.lower().startswith(cmdfix + 'resume'):
                        self.status = 'dnd'
                        yield from self.update_presence()
                        yield from self.send_message(msg.channel, 'Successfully **resumed** the bot\'s command and conversation processing!')
                elif myself in msg.mentions:
                    yield from self.auto_cb_convo(msg, self.user.mention)
                elif msg.channel.is_private:
                    if msg.content.split('\n')[0] == cmdfix:
                        yield from self.send_typing(msg.channel)
                        yield from self.send_message(msg.channel, self.ece_fmt.format(msg.author, '', cmdfix))
                    elif msg.content.startswith(cmdfix):
                        yield from self.send_typing(msg.channel)
                        yield from self.sprocess_commands(msg, cmdfix)
                    else:
                        yield from self.send_typing(msg.channel)
                        cb_reply = yield from self.askcb(msg.content)
                        yield from self.send_message(msg.channel, ':speech_balloon: ' + cb_reply)
                elif msg.content.lower().startswith(bname.lower() + ' '):
                    nmsg = self.bdel(msg.content.lower(), bname.lower())
                    for i in self.auto_convo_starters:
                        if nmsg.startswith(' ' + i):
                            yield from self.auto_cb_convo(msg, bname.lower() + ' ')
                        elif nmsg.endswith('?'):
                            yield from self.auto_cb_convo(msg, bname.lower() + ' ')
                        elif nmsg.startswith(', '):
                            yield from self.auto_cb_convo(msg, bname.lower() + ', ')
                        elif nmsg.startswith('... '):
                            yield from self.auto_cb_convo(msg, bname.lower() + '... ')
                else:
                    if msg.content.split('\n')[0] == cmdfix:
                        yield from self.send_typing(msg.channel)
                        yield from self.send_message(msg.channel, self.ece_fmt.format(msg.author, '', cmdfix))
                    elif msg.content.startswith(cmdfix):
                        yield from self.send_typing(msg.channel)
                        yield from self.sprocess_commands(msg, cmdfix)
        else:
            pass

    @asyncio.coroutine
    def suspend(self):
        """Suspend the bot."""
        self.status = 'invisible'
        yield from self.update_presence()

    @asyncio.coroutine
    def sprocess_commands(self, message, prefix):
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
        prefix : str
            Command prefix to use in context.
        """
        if self.status == 'invisible': return
        _internal_channel = message.channel
        _internal_author = message.author
        view = StringView(message.content)
        view.skip_string(prefix)
        cmd = view.get_word()
        tmp = {
            'bot': self,
            'invoked_with': cmd,
            'message': message,
            'view': view,
            'prefix': prefix
        }
        ctx = Context(**tmp)
        del tmp

        if cmd in self.commands:
            command = self.commands[cmd.lower()]
            self.dispatch('command', command, ctx)
            try:
                yield from command.invoke(ctx)
            except CommandError as exp:
                ctx.command.dispatch_error(exp, ctx)
            else:
                self.dispatch('command_completion', command, ctx)
        else:
            exc = CommandNotFound('Command "{}" is not found'.format(cmd))
            self.dispatch('command_error', exc, ctx)

    @asyncio.coroutine
    def send_typing(self, destination):
        """|coro|
        Send a *typing* status to the destination.
        *Typing* status will go away after 10 seconds, or after a message is sent.
        The destination parameter follows the same rules as :meth:`send_message`.
        Parameters
        ----------
        destination
            The location to send the typing update.
        """
        if self.status == 'invisible': return
        channel_id, guild_id = yield from self._resolve_destination(destination)
        yield from self.http.send_typing(channel_id)
