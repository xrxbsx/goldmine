"""The bot's ProBot subclass module, to operate the whole bot."""
import asyncio
import functools
import random
import inspect
import math
import logging
import discord
import discord.ext.commands as commands
from discord.ext.commands.bot import Context, StringView, CommandError, CommandNotFound, HelpFormatter
from google import search
from cleverbot import Cleverbot
from util.datastore import get_cmdfix, get_prop, set_prop
import util.ranks as rank
from util.const import *

class CleverQuery():
    def __init__(self, channel_to, query, prefix, suffix):
        self.destination = channel_to
        self.prefix = prefix
        self.suffix = suffix
        self.query = query

class ProBot(commands.Bot):
    """The brain of the bot, ProBot."""

    def __init__(self, **options):
        self.logger = logging.getLogger('discord').getChild('client')
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
        super().__init__(**options)

    async def cb_task(self, queue):
        """Handle the answering of all Cleverbot queries."""
        while True:
            queue.clear()
            current = await queue.get()
            cb_args = [
                current.destination,
                current.query,
                current.prefix,
                current.suffix,
                queue
            ]
            await self.cb_ask(*cb_args)
            await queue.wait()

    async def update_presence(self):
        """Generate an updated presence and change it."""
        self.presence = {
            'game': discord.Game(**self.game),
            'status': discord.Status(self.status)
        }
        await self.change_presence(**self.presence)

    async def sctx(self, ctx, msg):
        """Send a message to the context's message origin.'"""
        self.send_message(ctx.message.channel, msg)

    async def cb_ask(self, dest, query, prefix, suffix, queue):
        reply_bot = await self.askcb(query)
        await self.send_message(dest, prefix + reply_bot + suffix)
        await asyncio.sleep(2)
        queue.set()
    async def askcb(self, query):
        """A method of querying Cleverbot safe for async."""
        blocking_cb = self.loop.run_in_executor(None, self.cb.ask, query)
        tmp = await blocking_cb
        return tmp
    async def google(self, query, **kwargs):
        """A method of querying Google safe for async."""
        blocking_g = self.loop.run_in_executor(None, functools.partial(search, query, **kwargs))
        tmp = await blocking_g
        return tmp

    async def send(self, *apass, **kwpass):
        await self.send_message(*apass, **kwpass)
    async def msend(self, msg, *apass, **kwpass):
        await self.send_message(msg.channel, *apass, **kwpass)
    async def csend(self, ctx, *apass, **kwpass):
        await self.send_message(ctx.message.channel, *apass, **kwpass)

    async def on_command_error(self, exp, ctx):
        cmdfix = await get_cmdfix(ctx.message)
        cproc = ctx.message.content.split(' ')[0]
        cprocessed = cproc[len(cmdfix):]
        c_key = str(exp)
        bc_key = self.bdel(c_key, 'Command raised an exception: ')
        self.logger.error('s' + ctx.message.server.id + ': ' + str(type(exp)) + ' - ' + str(exp))
        if isinstance(exp, commands.CommandNotFound):
            await self.csend(ctx, cnf_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.NoPrivateMessage):
            await self.csend(ctx, npm_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.DisabledCommand):
            await self.csend(ctx, ccd_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.CommandInvokeError):
            if bc_key.startswith('CommandPermissionError: ' + cmdfix):
                await self.csend(ctx, cpe_fmt.format(ctx.message.author, cprocessed, cmdfix))
            elif bc_key.startswith('HTTPException: '):
                key = self.bdel(bc_key, 'HTTPException: ')
                if key.startswith('BAD REQUEST'):
                    key = self.bdel(bc_key, 'BAD REQUEST')
                    if key.endswith('Cannot send an empty message'):
                        await self.csend(ctx, emp_msg.format(ctx.message.author, cprocessed, cmdfix))
                    elif c_key.startswith('Command raised an exception: HTTPException: BAD REQUEST (status code: 400)'):
                        await self.csend(ctx, big_msg.format(ctx.message.author, cprocessed, cmdfix))
                    else:
                        await self.csend(ctx, msg_err.format(ctx.message.author, cprocessed, cmdfix, key))
                elif c_key.startswith('Command raised an exception: HTTPException: BAD REQUEST (status code: 400)'):
                    await self.csend(ctx, big_msg.format(ctx.message.author, cprocessed, cmdfix))
                else:
                    await self.csend(ctx, msg_err.format(ctx.message.author, cprocessed, cmdfix, key))
            elif bc_key.startswith('NameError: name '):
                key = self.bdel(bc_key, "NameError: name '")
                key = key.replace("' is not defined", '')
                await self.csend(ctx, nam_err.format(ctx.message.author, cprocessed, cmdfix, key.split("''")[0]))
            elif bc_key.startswith('TimeoutError:'):
                key = self.bdel(bc_key, 'TimeoutError:')
                await self.csend(ctx, tim_err.format(ctx.message.author, cprocessed, cmdfix))
            else:
                await self.csend(ctx, 'An internal error has occured!```' + bc_key + '```')
        elif isinstance(exp, commands.MissingRequiredArgument):
            await self.csend(ctx, not_arg.format(ctx.message.author, cprocessed, cmdfix, cmdfix + self.bdel(self.commands[cprocessed].help.split('\n')[-1:][0], 'Syntax: ')))
        elif isinstance(exp, commands.TooManyArguments):
            await self.csend(ctx, too_arg.format(ctx.message.author, cprocessed, cmdfix, cmdfix + self.bdel(self.commands[cprocessed].help.split('\n')[-1:][0], 'Syntax: ')))
        elif isinstance(exp, commands.BadArgument):
            await self.csend(ctx, bad_arg.format(ctx.message.author, cprocessed, cmdfix, cmdfix + self.bdel(self.commands[cprocessed].help.split('\n')[-1:][0], 'Syntax: ')))
        else:
            await self.csend(ctx, 'An internal error has occured!```' + bc_key + '```')

    def casein(self, substr, clist):
        """Return if a substring is found in any of clist."""
        for i in clist:
            if substr in i:
                return True
        return False

    @staticmethod
    def bdel(s, r): return (s[len(r):] if s.startswith(r) else s)

    async def oauto_cb_convo(self, msg, kickstart):
        """The old, broken auto conversation manager."""
        if self.status == 'invisible': return
        absid = msg.server.id + ':' + msg.channel.id + ':' + msg.author.id
        if absid not in self.auto_convos:
            await self.send_typing(msg.channel)
            self.auto_convos.append(absid)
            lmsg = msg.content.lower()
            reply = lmsg
            reply_bot = await self.askcb(self.bdel(lmsg, kickstart + ' ')) #ORIG
            await self.msend(msg, msg.author.mention + ' ' + reply_bot) #ORIG
#            cb_query = CleverQuery(msg.channel, self.bdel(lmsg, kickstart + ' '), msg.author.mention + ' ', '') #NEW
#            await self.main_cb_queue.put(cb_query) #NEW
            while self.casein('?', [reply_bot, reply]) or (reply_bot in q_replies):
                rep = await self.wait_for_message(author=msg.author)
                reply = rep.content
#                cb_query = CleverQuery(msg.channel, self.bdel(lmsg, kickstart + ' '), msg.author.mention + ' ', '') #NEW
#                await self.main_cb_queue.put(cb_query) #NEW
                reply_bot = await self.askcb(reply) #ORIG
                await self.msend(msg, msg.author.mention + ' ' + reply_bot) #ORIG
            self.auto_convos.remove(absid)
    async def auto_cb_convo(self, msg, kickstart, replace=False):
        """Current auto conversation manager."""
        if self.status == 'invisible': return
        await self.send_typing(msg.channel)
        lmsg = msg.content.lower()
        reply = lmsg
        if replace:
            cb_string = lmsg.replace(kickstart, '')
        else:
            cb_string = self.bdel(lmsg, kickstart)
        reply_bot = await self.askcb(cb_string)
        await self.msend(msg, msg.author.mention + ' ' + reply_bot)

    async def on_ready(self):
        """On_ready event for when the bot logs into Discord."""
        self.logger.info('Bot has logged into Discord, ID ' + self.user.id)
        await self.update_presence()

    async def on_member_join(self, member: discord.Member):
        """On_member_join event for newly joined members."""
        cemotes = member.server.emojis
        em_string = (': ' + ' '.join([str(i) for i in cemotes]) if len(cemotes) >= 1 else '')
        fmt = '''Welcome {0.mention} to **{1.name}**. Have a good time here! :wink:
If you need any help, contact someone with your :question::question:s.
Remember to use the custom emotes{2} for extra fun! You can access my help with {3}help.'''
        bc = await get_prop(member, 'broadcast_join')
        if str(bc).lower() in bool_true:
            await self.send_message(member.server, fmt.format(member, member.server,
                                                            em_string))
    async def on_member_remove(self, member: discord.Member):
        """On_member_remove event for members leaving."""
        fmt = '''Awww, **{0.mention}** has just left this server. Bye bye, **{0.mention}**!
**{1.name}** has now lost a {2}. We'll miss you! :bear:'''
        bc = await get_prop(member, 'broadcast_leave')
        if str(bc).lower() in bool_true:
            utype = ('bot' if member.bot else 'member')
            await self.send_message(member.server, fmt.format(member, member.server, utype))

    async def on_message(self, msg):
        cmdfix = await get_cmdfix(msg)
        bname = await get_prop(msg, 'bot_name')
        try:
            myself = msg.server.me
        except AttributeError:
            myself = self.user
        if msg.author.id != myself.id:
            if msg.author.bot:
                if self.status == 'invisible': return
                if str(msg.channel) == 'cleverbutts':
                    await asyncio.sleep((random.random()) * 2)
                    await self.send_typing(msg.channel)
                    #await self.main_cb_queue.put(CleverQuery(msg.channel, msg.content, '', ''))
                    reply_bot = await self.askcb(msg.content)
                    s_duration = (((len(reply_bot) / 10) * 1.5) + random.random()) - 0.2
                    await asyncio.sleep(s_duration / 2)
                    await self.send_typing(msg.channel)
                    await asyncio.sleep((s_duration / 2) - 0.4)
                    await self.msend(msg, reply_bot)
                    await asyncio.sleep(1)
            else:
                if not msg.channel.is_private:
                    int_name = await get_prop(msg, 'bot_name')
                    if msg.server.me.display_name != int_name:
                        sntn = await get_prop(msg, 'set_nick_to_name')
                        if isinstance(sntn, str):
                            sntn = sntn.lower()
                        if sntn in bool_true:
                            await self.change_nickname(msg.server.me, int_name)
                    if not msg.content.startswith(cmdfix):
                        prof_name = 'profile_' + msg.server.id
                        prof = await get_prop(msg, prof_name)
                        prof['exp'] += math.ceil(((len(msg.content) / 6) * 1.5) + random.randint(0, 14))
                        new_level = rank.xp_level(prof['exp'])[0]
                        if new_level > prof['level']:
                            bclu = await get_prop(msg, 'broadcast_level_up')
                            if isinstance(bclu, str):
                                bclu = bclu.lower()
                            if bclu in bool_true:
                                await self.msend(msg, '**Hooray!** {0.mention} has just *advanced to* **level {1}**! Nice! Gotta get to **level {2}** now! :stuck_out_tongue:'.format(msg.author, str(new_level), str(new_level + 1)))
                        prof['level'] = new_level
                        await set_prop(msg, 'by_user', prof_name, prof)
                    if self.status == 'invisible': return
                    if str(msg.channel) == 'cleverbutts':
                        if msg.content.lower() == 'kickstart':
                            await self.msend(msg, 'Hi, how are you doing?')
                            return
                if self.status == 'invisible':
                    if msg.content.lower().startswith(cmdfix + 'resume'):
                        self.status = 'dnd'
                        await self.update_presence()
                        await self.msend(msg, 'Successfully **resumed** the bot\'s command and conversation processing!')
                elif myself.mentioned_in(msg):
                    await self.auto_cb_convo(msg, self.user.mention, replace=True)
                elif msg.channel.is_private:
                    if msg.content.split('\n')[0] == cmdfix:
                        await self.send_typing(msg.channel)
                        await self.msend(msg, ece_fmt.format(msg.author, '', cmdfix))
                    elif msg.content.startswith(cmdfix):
                        await self.send_typing(msg.channel)
                        await self.sprocess_commands(msg, cmdfix)
                    else:
                        await self.send_typing(msg.channel)
                        cb_reply = await self.askcb(msg.content)
                        await self.msend(msg, ':speech_balloon: ' + cb_reply)
                elif msg.content.lower().startswith(bname.lower() + ' '):
#                    nmsg = self.bdel(msg.content.lower(), bname.lower())
                    await self.auto_cb_convo(msg, bname.lower() + ' ')
                    '''
                    for i in auto_convo_starters:
                        if nmsg.startswith(' ' + i):
                            await self.auto_cb_convo(msg, bname.lower() + ' ')
                        elif nmsg.endswith('?'):
                            await self.auto_cb_convo(msg, bname.lower() + ' ')
                        elif nmsg.startswith(', '):
                            await self.auto_cb_convo(msg, bname.lower() + ', ')
                        elif nmsg.startswith('... '):
                            await self.auto_cb_convo(msg, bname.lower() + '... ')'''
                else:
                    if msg.content.split('\n')[0] == cmdfix:
                        await self.send_typing(msg.channel)
                        await self.msend(msg, ece_fmt.format(msg.author, '', cmdfix))
                    elif msg.content.startswith(cmdfix):
                        await self.send_typing(msg.channel)
                        await self.sprocess_commands(msg, cmdfix)
        else:
            pass

    async def suspend(self):
        """Suspend the bot."""
        self.status = 'invisible'
        await self.update_presence()

    async def sprocess_commands(self, message, prefix):
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
        cl = cmd.lower().replace('é', 'e') # TODO: Real accent parsing

        if cl in self.commands:
            command = self.commands[cl]
            self.dispatch('command', command, ctx)
            try:
                await command.invoke(ctx)
                if ctx.message.content == prefix + 'help':
                    await self.send_message(message.channel, message.author.mention + ' **__I\'ve private messaged you my help and commands, please check your DMs!__** :smiley: Hope you enjoy.')
            except CommandError as exp:
                ctx.command.dispatch_error(exp, ctx)
            else:
                self.dispatch('command_completion', command, ctx)
        else:
            exc = CommandNotFound('Command "{}" is not found'.format(cmd))
            self.dispatch('command_error', exc, ctx)

    async def send_typing(self, destination):
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
        channel_id, guild_id = await self._resolve_destination(destination)
        await self.http.send_typing(channel_id)
