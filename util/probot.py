"""The bot's ProBot subclass module, to operate the whole bot."""
import asyncio
import functools
import random
import inspect
import subprocess
import os
import sys
import re
from fnmatch import filter
from datetime import datetime
import math
import logging
import discord
import util.commands as commands
from .commands.bot import Context, StringView, CommandError, CommandNotFound
from google import search
from cleverbot import Cleverbot
import pickledb
from convert_to_old_syntax import cur_dir, rc_files
from properties import storage_backend
from util.datastore import get_cmdfix, get_prop, set_prop, f_exts
import util.ranks as rank
from util.const import *
from util.func import bdel

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
        self.perm_mask = '1609825363' # 66321741 = full
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
        self.chars = 0
        self.words = 0
        self.lines = 0
        self.files = 0
        self.size_bytes = 0
        self.raw_sizes_bytes = []
        self.size_kb = 0
        self.avg_size_bytes = 0
        self.avg_size_kb = 0
        for fn in filter(rc_files(cur_dir), '*.py'):
            with open(fn, 'rb') as f: # fix for windows unicode error
                fr = f.read().decode('utf-8') # fix for windows unicode error
                self.chars += len(fr)
                self.words += len(fr.split(' '))
                self.lines += len(fr.split('\n'))
                self.files += 1
            self.raw_sizes_bytes.append(os.path.getsize(fn))
        self.size_bytes = sum(self.raw_sizes_bytes)
        self.avg_size_bytes = self.size_bytes / self.files
        self.size_kb = self.size_bytes / 1000
        self.avg_size_kb = self.size_kb / self.files
        self.git_rev = 'Couldn\'t fetch'
        try:
            self.git_rev = subprocess.check_output(['git', 'describe', '--always']).decode('utf-8')
        except subprocess.CalledProcessError:
            pass
        self.start_time = datetime.now()
        self.dir = os.path.dirname(os.path.realpath(__file__))
        self.storepath = os.path.join(self.dir, '..', 'storage.')
        try:
            self.storepath += f_exts[storage_backend]
        except KeyError:
            self.logger.critical('Invalid storage backend specified, quitting!')
            exit(1)
        self.version = '0.0.1'
        with open(os.path.join(cur_dir, '__init__.py')) as f:
            self.version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)
        self.storage = None
        if storage_backend == 'leveldb':
            import plyvel
            self.storage = plyvel.xp_level
        elif storage_backend == 'pickledb':
            self.storage = pickledb.load(self.storepath, False)
        self.modules = sys.modules
        self.continued_index_errors = 0
        self.dc_ver = discord.version_info
        self.lib_version = '.'.join([str(i) for i in self.dc_ver])
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
        bc_key = bdel(c_key, 'Command raised an exception: ')
        eprefix = 's'
        try:
            cmid = ctx.message.server.id
        except AttributeError:
            cmid = ctx.message.author.id
            eprefix = 'dm'
        self.logger.error(eprefix + cmid + ': ' + str(type(exp)) + ' - ' + str(exp))
        if isinstance(exp, commands.NoPrivateMessage):
            await self.csend(ctx, npm_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.CommandNotFound):
            pass
#            await self.csend(ctx, cnf_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.DisabledCommand):
            await self.csend(ctx, ccd_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.CommandOnCooldown):
            await self.send_message(exp.ctx.message.author, coc_fmt.format(ctx.message.author, cprocessed, cmdfix, bdel(c_key, 'You are on cooldown. Try again in ')))
        elif isinstance(exp, commands.CommandInvokeError):
            if bc_key.startswith('CommandPermissionError: ' + cmdfix):
                _perms = ''
                if exp.original.perms_required:
                    _perms = ', '.join([i.replace('_', ' ').title() for i in exp.original.perms_required])
                else:
                    _perms = 'Not specified'
                await self.csend(ctx, cpe_fmt.format(ctx.message.author, cprocessed, cmdfix, _perms))
            elif bc_key.startswith('HTTPException: '):
                key = bdel(bc_key, 'HTTPException: ')
                if key.startswith('BAD REQUEST'):
                    key = bdel(bc_key, 'BAD REQUEST')
                    if key.endswith('Cannot send an empty message'):
                        await self.csend(ctx, emp_msg.format(ctx.message.author, cprocessed, cmdfix))
                    elif c_key.startswith('Command raised an exception: HTTPException: BAD REQUEST (status code: 400)'):
                        if (eprefix == 'dm') and (ctx.invoked_with == 'user'):
                            await self.csend(ctx, '**No matching users, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!**')
                        else:
                            await self.csend(ctx, big_msg.format(ctx.message.author, cprocessed, cmdfix))
                    else:
                        await self.csend(ctx, msg_err.format(ctx.message.author, cprocessed, cmdfix, key))
                elif c_key.startswith('Command raised an exception: HTTPException: BAD REQUEST (status code: 400)'):
                    if (eprefix == 'dm') and (ctx.invoked_with == 'user'):
                        await self.csend(ctx, '**No matching users, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!**')
                    else:
                        await self.csend(ctx, big_msg.format(ctx.message.author, cprocessed, cmdfix))
                else:
                    await self.csend(ctx, msg_err.format(ctx.message.author, cprocessed, cmdfix, key))
            elif bc_key.startswith('NameError: name '):
                key = bdel(bc_key, "NameError: name '")
                key = key.replace("' is not defined", '')
                await self.csend(ctx, nam_err.format(ctx.message.author, cprocessed, cmdfix, key.split("''")[0]))
            elif bc_key.startswith('TimeoutError:'):
                key = bdel(bc_key, 'TimeoutError:')
                await self.csend(ctx, tim_err.format(ctx.message.author, cprocessed, cmdfix))
            elif (cprocessed in self.commands['calc'].aliases) or (cprocessed == 'calc'):
                if bc_key.startswith('ValueError: ('):
                    pass
                else:
                    key = bdel(bc_key, 'SyntaxError: invalid syntax (<unknown>, line ')
                    key = bdel(bc_key, 'TypeError: <_ast.')
                    await self.csend(ctx, ast_err.format(ctx.message.author, cprocessed, cmdfix))
            else:
                await self.csend(ctx, 'An internal error occured while responding to `%s`!```' % (cmdfix + cprocessed) + bc_key + '```')
        elif isinstance(exp, commands.MissingRequiredArgument):
            await self.csend(ctx, not_arg.format(ctx.message.author, cprocessed, cmdfix, cmdfix + bdel(self.commands[cprocessed].help.split('\n')[-1:][0], 'Syntax: ')))
        elif isinstance(exp, commands.TooManyArguments):
            await self.csend(ctx, too_arg.format(ctx.message.author, cprocessed, cmdfix, cmdfix + bdel(self.commands[cprocessed].help.split('\n')[-1:][0], 'Syntax: ')))
        elif isinstance(exp, commands.BadArgument):
            await self.csend(ctx, bad_arg.format(ctx.message.author, cprocessed, cmdfix, cmdfix + bdel(self.commands[cprocessed].help.split('\n')[-1:][0], 'Syntax: ')))
        else:
            await self.csend(ctx, 'An internal error occured while responding to` %s`!```' % (cmdfix + cprocessed) + bc_key + '```')

    def casein(self, substr, clist):
        """Return if a substring is found in any of clist."""
        for i in clist:
            if substr in i:
                return True
        return False

    async def oauto_cb_convo(self, msg, kickstart):
        """The old, broken auto conversation manager."""
        if self.status == 'invisible': return
        absid = msg.server.id + ':' + msg.channel.id + ':' + msg.author.id
        if absid not in self.auto_convos:
            await self.send_typing(msg.channel)
            self.auto_convos.append(absid)
            lmsg = msg.content.lower()
            reply = lmsg
            reply_bot = await self.askcb(bdel(lmsg, kickstart + ' ')) #ORIG
            await self.msend(msg, msg.author.mention + ' ' + reply_bot) #ORIG
#            cb_query = CleverQuery(msg.channel, bdel(lmsg, kickstart + ' '), msg.author.mention + ' ', '') #NEW
#            await self.main_cb_queue.put(cb_query) #NEW
            while self.casein('?', [reply_bot, reply]) or (reply_bot in q_replies):
                rep = await self.wait_for_message(author=msg.author)
                reply = rep.content
#                cb_query = CleverQuery(msg.channel, bdel(lmsg, kickstart + ' '), msg.author.mention + ' ', '') #NEW
#                await self.main_cb_queue.put(cb_query) #NEW
                reply_bot = await self.askcb(reply) #ORIG
                await self.msend(msg, msg.author.mention + ' ' + reply_bot) #ORIG
            self.auto_convos.remove(absid)
    async def auto_cb_convo(self, msg, kickstart, replace=False):
        """Current auto conversation manager."""
        if self.status == 'invisible': return
        await self.send_typing(msg.channel)
        lmsg = msg.content.lower().replace('@everyone', '').replace('@here', '')
        reply = lmsg
        if replace:
            cb_string = lmsg.replace(kickstart, '')
        else:
            cb_string = bdel(lmsg, kickstart)
        reply_bot = await self.askcb(cb_string)
        await self.msend(msg, msg.author.mention + ' ' + reply_bot)

    async def on_ready(self):
        """On_ready event for when the bot logs into Discord."""
        self.logger.info('Bot has logged into Discord, ID ' + self.user.id)
        await self.update_presence()

    async def on_member_join(self, member: discord.Member):
        """On_member_join event for newly joined members."""
        cemotes = member.server.emojis
        em_string = ''
        if cemotes:
            em_string = ': ' + ' '.join([str(i) for i in cemotes])
        fmt = '''Welcome {0.mention} to **{1.name}**. Have a good time here! :wink:
If you need any help, contact someone with your :question::question:s.
Remember to use the custom emotes{2} for extra fun! You can access my help with {3}help.'''
        bc = await get_prop(member, 'broadcast_join')
        cmdfix = await get_prop(member, 'command_prefix')
        if str(bc).lower() in bool_true:
            await self.send_message(member.server, fmt.format(member, member.server, em_string, cmdfix))
    async def on_member_remove(self, member: discord.Member):
        """On_member_remove event for members leaving."""
        fmt = '''Aw, **{0}** has just left this server. Bye!
**{1.name}** has now lost a {2}. We'll miss you! :bear:'''
        bc = await get_prop(member, 'broadcast_leave')
        if str(bc).lower() in bool_true:
            utype = ('bot' if member.bot else 'member')
            await self.send_message(member.server, fmt.format(str(member), member.server, utype))

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
                                await self.msend(msg, '**Hooray!** {0.mention} has just *advanced to* **level {1}**. Nice! Gotta get to **level {2}** now :stuck_out_tongue:'.format(msg.author, str(new_level), str(new_level + 1)))
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
                elif myself.mentioned_in(msg) and ('@everyone' not in msg.content) and ('@here' not in msg.content):
                    await self.auto_cb_convo(msg, self.user.mention, replace=True)
                elif msg.channel.is_private:
#                    if msg.content.split('\n')[0] == cmdfix:
#                        await self.send_typing(msg.channel)
#                        await self.msend(msg, ece_fmt.format(msg.author, '', cmdfix))
                    if msg.content.startswith(cmdfix):
                        await self.sprocess_commands(msg, cmdfix)
                    else:
                        await self.send_typing(msg.channel)
                        cb_reply = await self.askcb(msg.content)
                        await self.msend(msg, ':speech_balloon: ' + cb_reply)
                elif msg.content.lower().startswith(bname.lower()):
#                    nmsg = bdel(msg.content.lower(), bname.lower())
                    await self.auto_cb_convo(msg, bname.lower())
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
                elif msg.content == 'prefix':
                    await self.msend(msg, '**Current server command prefix is: **`' + cmdfix + '`')
                else:
#                    if msg.content.split('\n')[0] == cmdfix:
#                        await self.send_typing(msg.channel)
#                        await self.msend(msg, ece_fmt.format(msg.author, '', cmdfix))
                    if msg.content.startswith(cmdfix):
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
        cl = cmd.lower().replace('é', 'e').replace('è', 'e') # TODO: Real accent parsing

        if cl in self.commands:
            await self.send_typing(message.channel)
            command = self.commands[cl]
            self.dispatch('command', command, ctx)
            try:
                await command.invoke(ctx)
                if ctx.message.content == prefix + 'help':
                    await self.send_message(message.channel, message.author.mention + ' **__I\'ve private messaged you my help, please check your DMs!__**')
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

    async def format_uptime(self):
        def s(num):
            return 's' if (num == 0) or (num > 1) else ''
        fmt = '{0} day{4} {1} hour{5} {2} minute{6} {3} second{7}'
        time_diff = datetime.now() - self.start_time
        time_mins = divmod(time_diff.total_seconds(), 60)
        time_hrs = divmod(time_mins[0], 60)
        time_days = divmod(time_hrs[0], 24)
        final = fmt.format(int(time_days[0]), int(time_days[1]), int(time_hrs[1]), int(time_mins[1]),
                           s(time_days[0]), s(time_days[1]), s(time_hrs[1]), s(time_mins[1]))
        return final
