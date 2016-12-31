"""The bot's ProBot subclass module, to operate the whole bot."""
import asyncio
import random
import inspect
import subprocess
from contextlib import suppress
import os
import sys
import traceback
import re
import shutil
from collections import deque
from fnmatch import filter
from datetime import datetime
import math
import logging
import aiohttp
import async_timeout
from asteval import Interpreter
import discord
import util.commands as commands
from .commands.bot import ProContext, StringView, CommandError, CommandNotFound
from util.google import search
from util.cleverbot import Cleverbot
import pickledb
from convert_to_old_syntax import cur_dir, rc_files
from properties import storage_backend
from util.datastore import DataStore
import util.ranks as rank
from util.const import *
from util.func import bdel
from util.fake import FakeObject
import util.json as json

try:
    from d_props import store_path
    opath = store_path
except ImportError:
    opath = None
try:
    import speech_recognition as sr
    r = sr.Recognizer()
except ImportError:
    r = None
try:
    from opuslib import Decoder
except Exception:
    Decoder = None

if sys.platform in ['linux', 'linux2', 'darwin']:
    import resource

arg_err_map = {
    commands.MissingRequiredArgument: 'out enough arguments',
    commands.BadArgument: ' an invalid argument',
    commands.TooManyArguments: ' too many arguments'
}

class ProBot(commands.Bot):
    """The brain of the bot, ProBot."""

    def __init__(self, **options):
        self.logger = logging.getLogger('bot')
        self.cb = Cleverbot()
        self.is_restart = False
        self.loop = asyncio.get_event_loop()
        self.perm_mask = '1609825363' # 66321741 = full
        self.game = {
            'name': 'Dragon Essence',
            'type': 1,
            'url': 'https://www.twitch.tv/dragon5232'
        }
        self.status = 'online'
        self.presence = {}
        self.chars = 0
        self.words = 0
        self.lines = 0
        self.files = 0
        self.size_bytes = 0
        self.raw_sizes_bytes = set()
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
            self.raw_sizes_bytes.add(os.path.getsize(fn))
        self.size_bytes = sum(self.raw_sizes_bytes)
        self.avg_size_bytes = self.size_bytes / self.files
        self.size_kb = self.size_bytes / 1000
        self.avg_size_kb = self.size_kb / self.files
        self.git_rev = 'Couldn\'t fetch'
        try:
            self.git_rev = subprocess.check_output(['git', 'describe', '--always']).decode('utf-8')
        except Exception:
            pass
        self.start_time = datetime.now()
        self.dir = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
        self.storepath = os.path.join(self.dir, 'storage.')
        if storage_backend not in DataStore.exts:
            self.logger.critical('Invalid storage backend specified, quitting!')
        self.version = '0.0.1'
        with open(os.path.join(cur_dir, '__init__.py')) as f:
            self.version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)
        self.store = None
        if opath:
            self.store = DataStore(storage_backend, path=opath, join_path=False)
        else:
            self.store = DataStore(storage_backend)
        self.storage = None
        if storage_backend == 'leveldb':
            import plyvel
            self.storage = plyvel.load()
        elif storage_backend == 'pickledb':
            self.storage = pickledb.load(self.storepath, False)
        self.modules = sys.modules
        self.continued_index_errors = 0
        self.dc_ver = discord.version_info
        self.lib_version = '.'.join([str(i) for i in self.dc_ver])
        self.store_writer = self.loop.create_task(self.store.commit_task())
        self.cleverbutt_timers = set()
        self.cleverbutt_latest = {}
        self.asteval = Interpreter(use_numpy=False, writer=FakeObject(value=True))
        self.have_resource = False
        if sys.platform in ['linux', 'linux2', 'darwin']:
            self.have_resource = True
        if Decoder:
            self.opus_decoder = Decoder(48000, 2)
        else:
            self.opus_decoder = None
        self.pcm_data = {}
        self.servers_recording = set()
        self.cleverbutt_replied_to = set()
        self.get_emote_task = asyncio.ensure_future(self.update_emote_data())
        self.emotes = {}
        self.dl_cogs_path = os.path.join(self.dir, 'cogs')
        self.ex_cogs_path = os.path.join(self.dir, 'cogs.txt')
        self.dis_cogs_path = os.path.join(self.dir, 'disabled_cogs.txt')
        self.init_dl_cogs_path = os.path.join(self.dir, 'cogs', '__init__.py')
        self.data_cogs_path = os.path.join(self.dir, 'data')
        self.cog_json_cogs_path = os.path.join(self.dir, 'data', 'cogs.json')
        self.cogs_cog_py_path = os.path.join(self.dir, 'cogs', 'cog.py')
        for name in ['dl', 'data']: # Dirs
            p = getattr(self, name + '_cogs_path')
            with suppress(OSError):
                if not os.path.exists(p):
                    os.makedirs(p)
        for name in ['ex', 'dis']: # Files
            p = getattr(self, name + '_cogs_path')
            with suppress(OSError):
                if not os.path.exists(p):
                    f = open(p, 'a')
                    f.close()
        with suppress(OSError):
            if not os.path.exists(self.init_dl_cogs_path):
                with open(self.init_dl_cogs_path, 'w+') as f:
                    f.write('"""Placeholder to make Python recognize this as a module."""\n')
        with suppress(IOError):
            if not os.path.exists(self.cogs_cog_py_path):
                shutil.copy2(os.path.join(self.dir, 'default_cogs', 'cog.py'), self.cogs_cog_py_path)
        self.disabled_cogs = []
        with open(self.dis_cogs_path, 'r') as f:
            self.disabled_cogs = [c.replace('\n', '').replace('\r', '') for c in f.readlines()]
        self.enabled_cogs = []
        with open(self.ex_cogs_path, 'r') as f:
            self.enabled_cogs = [c.replace('\n', '').replace('\r', '') for c in f.readlines()]
        if not os.path.exists(self.cog_json_cogs_path):
            with open(self.cog_json_cogs_path, 'a') as f:
                f.write('{}')
        super().__init__(**options)

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

    async def askcb(self, query):
        """A method of querying Cleverbot safe for async."""
        return await self.cb.ask(query) # now just an alias
    async def google(self, query, num=3):
        """A method of querying Google safe for async."""
        return await search(query, num=num)

    async def send(self, *apass, **kwpass):
        await self.send_message(*apass, **kwpass)
    async def msend(self, msg, *apass, **kwpass):
        await self.send_message(msg.channel, *apass, **kwpass)
    async def csend(self, ctx, *apass, **kwpass):
        await self.send_message(ctx.message.channel, *apass, **kwpass)

    async def on_command_error(self, exp, ctx):
        cmdfix = await self.store.get_cmdfix(ctx.message)
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
        if isinstance(exp, commands.CommandNotFound):
            self.logger.error(str(ctx.message.author) + ' in ' + ctx.message.server.name + ': command \'' + cprocessed + '\' not found')
        elif isinstance(exp, commands.CommandInvokeError):
            self.logger.error(str(ctx.message.author) + ' in ' + ctx.message.server.name + f': [cmd {cprocessed}] ' + bc_key)
            traceback.print_exception(type(exp.original), exp.original, exp.original.__traceback__, file=sys.stdout)
            raise exp
        else:
            self.logger.error(str(ctx.message.author) + ' in ' + ctx.message.server.name + ': ' + str(exp) + ' (%s)' % type(exp).__name__)
            traceback.print_exception(type(exp), exp, exp.__traceback__, file=sys.stdout)
        if isinstance(exp, commands.NoPrivateMessage):
            await self.csend(ctx, npm_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.CommandNotFound):
            pass
#            await self.csend(ctx, cnf_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.DisabledCommand):
            await self.csend(ctx, ccd_fmt.format(ctx.message.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.CommandOnCooldown):
            await self.send_message(exp.ctx.message.author, coc_fmt.format(ctx.message.author, cprocessed, cmdfix, bdel(c_key, 'You are on cooldown. Try again in ')))
        elif isinstance(exp, commands.PassException):
            pass
        elif isinstance(exp, commands.ReturnError):
            await self.csend(ctx, exp.text)
        elif isinstance(exp, commands.CommandPermissionError):
            _perms = ''
            if exp.perms_required:
                perm_list = [i.lower().replace('_', ' ').title() for i in exp.perms_required]
                if len(perm_list) > 1:
                    perm_list[-1] = '**and **' + perm_list[-1] # to cancel bold
                _perms = ', '.join(perm_list)
            else:
                _perms = 'Not specified'
            await self.csend(ctx, cpe_fmt.format(ctx.message.author, cprocessed, cmdfix, _perms))
        elif isinstance(exp, commands.OrCommandPermissionError):
            _perms = ''
            if exp.perms_ok:
                perm_list = [i.lower().replace('_', ' ').title() for i in exp.perms_ok]
                if len(perm_list) > 1:
                    perm_list[-1] = '**or **' + perm_list[-1] # to cancel bold
                _perms = ', '.join(perm_list)
            else:
                _perms = 'Not specified'
            await self.csend(ctx, ocpe_fmt.format(ctx.message.author, cprocessed, cmdfix, _perms))
        elif isinstance(exp, commands.CommandInvokeError):
            if isinstance(exp.original, discord.HTTPException):
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
                elif c_key.startswith('Command raised an exception: RuntimeError: PyNaCl library needed in order to use voice'):
                    await self.csend(ctx, '**The bot owner hasn\'t enabled voice!**')
                else:
                    await self.csend(ctx, msg_err.format(ctx.message.author, cprocessed, cmdfix, key))
            elif isinstance(exp.original, NameError):
                if isinstance(exp.original, UnboundLocalError):
                    key = bdel(bc_key, "UnboundLocalError: local variable '")
                    key = key.replace("' referenced before assignment", '')
                    await self.csend(ctx, nam_err.format(ctx.message.author, cprocessed, cmdfix, key))
                else:
                    key = bdel(bc_key, "NameError: name '")
                    key = key.replace("' is not defined", '')
                    await self.csend(ctx, nam_err.format(ctx.message.author, cprocessed, cmdfix, key.split("''")[0]))
            elif isinstance(exp.original, asyncio.TimeoutError):
                await self.csend(ctx, tim_err.format(ctx.message.author, cprocessed, cmdfix))
            elif (cprocessed in self.commands['calc'].aliases) or (cprocessed == 'calc'):
                await self.csend(ctx, ast_err.format(ctx.message.author, cprocessed, cmdfix))
            else:
                await self.csend(ctx, 'An internal error occured while responding to `%s`!\n```' % (cmdfix + cprocessed) + bc_key + '```')
        elif type(exp) in [commands.MissingRequiredArgument, commands.TooManyArguments, commands.BadArgument]:
            if ctx.invoked_subcommand is None:
                tgt_cmd = self.commands[cprocessed]
            else:
                tgt_cmd = ctx.invoked_subcommand
            await self.csend(ctx, arg_err.format(ctx.message.author, cprocessed, cmdfix, cmdfix +
                             cprocessed + bdel(bdel(bdel(tgt_cmd.help.split('\n')[-1], 'Usage: '),
                             tgt_cmd.name), cprocessed), arg_err_map[type(exp)]))
        else:
            await self.csend(ctx, 'An internal error occured while responding to` %s`!\n```' % (cmdfix + cprocessed) + bc_key + '```')

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
            self.auto_convos.add(absid)
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
        target = member.server
        cemotes = member.server.emojis
        em_string = ''
        if cemotes:
            em_string = ': ' + ' '.join([str(i) for i in cemotes])
        fmt = '''Welcome {0.mention} to **{1.name}**. Have a good time here! :wink:
Remember to use the custom emotes{2} for extra fun! You can access my help with {3}help.'''
        bc = await self.store.get_prop(member, 'broadcast_join')
        cmdfix = await self.store.get_prop(member, 'command_prefix')
        if str(bc).lower() in bool_true:
            try:
                await self.send_message(target, fmt.format(member, member.server, em_string, cmdfix))
            except discord.Forbidden:
                self.logger.warning(f'Couldn\'t broadcast join of {member} to {member.server}')
    async def on_member_remove(self, member: discord.Member):
        """On_member_remove event for members leaving."""
        target = member.server
        fmt = '''Aw, **{0}** has just left this server. Bye!
**{1.name}** has now lost a {2}. We'll miss you! :bear:'''
        bc = await self.store.get_prop(member, 'broadcast_leave')
        if str(bc).lower() in bool_true:
            utype = ('bot' if member.bot else 'member')
            try:
                await self.send_message(target, fmt.format(str(member), member.server, utype))
            except discord.Forbidden:
                self.logger.warning(f'Couldn\'t broadcast leave of {member} from {member.server}')

    async def clever_reply(self, msg):
        self.cleverbutt_timers.add(msg.server.id)
        await asyncio.sleep((random.random()) * 2)
        await self.send_typing(msg.channel)
        try:
            query = self.cleverbutt_latest[msg.server.id]
        except KeyError:
            query = msg.content
        reply_bot = await self.askcb(query)
        s_duration = (((len(reply_bot) / 15) * 1.4) + random.random()) - 0.2
        await asyncio.sleep(s_duration / 2)
        await self.send_typing(msg.channel)
        await asyncio.sleep((s_duration / 2) - 0.4)
        await self.msend(msg, reply_bot)
        await asyncio.sleep(1)
        try:
            del self.cleverbutt_latest[msg.server.id]
        except Exception:
            pass
        self.cleverbutt_replied_to.add(msg.id)
        self.cleverbutt_timers.remove(msg.server.id)

    async def on_message(self, msg):
        cmdfix = await self.store.get_cmdfix(msg)
        bname = await self.store.get_prop(msg, 'bot_name')
        prefix_convo = bool((await self.store.get_prop(msg, 'prefix_answer')) in bool_true)
        try:
            myself = msg.server.me
        except AttributeError:
            myself = self.user
        if msg.author.id != myself.id:
            if msg.author.bot:
                if self.status == 'invisible': return
                if str(msg.channel) == 'cleverbutts':
                    if msg.server.id in self.cleverbutt_timers: # still on timer for next response
                        self.cleverbutt_latest[msg.server.id] = msg.content
                        await asyncio.sleep(4.5)
                        if msg.id not in self.cleverbutt_replied_to:
                            await self.clever_reply(msg)
                    else:
                        await self.clever_reply(msg)
            else:
                if not msg.channel.is_private:
                    int_name = await self.store.get_prop(msg, 'bot_name')
                    if msg.server.me.display_name != int_name:
                        sntn = await self.store.get_prop(msg, 'set_nick_to_name')
                        if isinstance(sntn, str):
                            sntn = sntn.lower()
                        if sntn in bool_true:
                            await self.change_nickname(msg.server.me, int_name)
                    if not msg.content.startswith(cmdfix):
                        prof_name = 'profile_' + msg.server.id
                        prof = await self.store.get_prop(msg, prof_name)
                        prof['exp'] += math.ceil(((len(msg.content) / 6) * 1.5) + random.randint(0, 14))
                        new_level = rank.xp_level(prof['exp'])[0]
                        if self.status != 'invisible':
                            if new_level > prof['level']:
                                bclu = await self.store.get_prop(msg, 'broadcast_level_up')
                                if isinstance(bclu, str):
                                    bclu = bclu.lower()
                                if bclu in bool_true:
                                    await self.msend(msg, '**Hooray!** {0.mention} has just *advanced* to **level {1}**.'.format(msg.author, str(new_level)))
                        prof['level'] = new_level
                        await self.store.set_prop(msg, 'by_user', prof_name, prof)
                    if str(msg.channel) == 'cleverbutts':
                        if self.status == 'invisible': return
                        if msg.content.lower() == 'kickstart':
                            await self.msend(msg, 'Hi, how are you doing?')
                            return
                if self.status == 'invisible':
                    if msg.content.lower().startswith(cmdfix + 'resume'):
                        self.status = 'dnd'
                        await self.update_presence()
                        await self.msend(msg, 'Successfully **resumed** my features!')
                elif myself.mentioned_in(msg) and ('@everyone' not in msg.content) and ('@here' not in msg.content):
                    await self.auto_cb_convo(msg, self.user.mention, replace=True)
                elif msg.channel.is_private:
#                    if msg.content.split('\n')[0] == cmdfix:
#                        await self.send_typing(msg.channel)
#                        await self.msend(msg, ece_fmt.format(msg.author, '', cmdfix))
                    if msg.content.startswith(cmdfix):
                        await self.process_commands(msg, cmdfix)
                    else:
                        await self.send_typing(msg.channel)
                        cb_reply = await self.askcb(msg.content)
                        await self.msend(msg, ':speech_balloon: ' + cb_reply)
                elif (msg.content.lower().startswith(bname.lower())) and (prefix_convo):
                    await self.auto_cb_convo(msg, bname.lower())
                elif msg.content == 'prefix':
                    await self.msend(msg, '**Current server command prefix is: **`' + cmdfix + '`')
                else:
#                    if msg.content.split('\n')[0] == cmdfix:
#                        await self.send_typing(msg.channel)
#                        await self.msend(msg, ece_fmt.format(msg.author, '', cmdfix))
                    if msg.content.startswith(cmdfix):
                        await self.process_commands(msg, cmdfix)
        else:
            pass

    async def on_error(self, ev_name, *ev_args, **ev_kwargs):
        kw_args = ', ' + (', '.join([k + '=' + str(ev_kwargs[k]) for k in ev_kwargs])) if ev_kwargs else ''
        self.logger.error(f'Event handler {ev_name} errored! Called with ' +
                          ', '.join([bdel(str(i), 'Command raised an exception: ') for i in ev_args]) + kw_args)

    async def on_server_join(self, server):
        """Send the bot introduction message when invited."""
        try:
            await self.send_message(server.default_channel, join_msg)
        except discord.Forbidden:
            satisfied = False
            c_count = 0
            try_channels = list(server.channels)
            channel_count = len(try_channels) - 1
            while not satisfied:
                with suppress(discord.Forbidden, discord.HTTPException):
                    await self.send_message(try_channels[c_count], join_msg)
                    satisfied = True
                if c_count > channel_count:
                    self.logger.warning('Couldn\'t announce join to server ' + server.name)
                    satisfied = True
                c_count += 1

    async def on_speaking(self, speaking, uid):
        """Event for when someone is speaking."""
        pass

    async def on_speak(self, data, timestamp, voice):
        """Event for when a voice packet is received."""
        if voice.server.id in self.servers_recording:
            decoded_data = await self.loop.run_in_executor(None, self.opus_decoder.decode, data, voice.encoder.frame_size)
            try:
                self.pcm_data[voice.server.id] += decoded_data
            except KeyError:
                self.pcm_data[voice.server.id] = decoded_data

    async def suspend(self):
        """Suspend the bot."""
        self.status = 'invisible'
        await self.update_presence()

    async def process_commands(self, message, prefix):
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
        ctx = ProContext(**tmp)
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

    async def send_message(self, destination, content=None, *, tts=False, embed=None):
        """|coro|
        Sends a message to the destination given with the content given.
        The destination could be a :class:`Channel`, :class:`PrivateChannel` or :class:`Server`.
        For convenience it could also be a :class:`User`. If it's a :class:`User` or :class:`PrivateChannel`
        then it sends the message via private message, otherwise it sends the message to the channel.
        If the destination is a :class:`Server` then it's equivalent to calling
        :attr:`Server.default_channel` and sending it there.
        If it is a :class:`Object` instance then it is assumed to be the
        destination ID. The destination ID is a *channel* so passing in a user
        ID will not be a valid destination.
        .. versionchanged:: 0.9.0
            ``str`` being allowed was removed and replaced with :class:`Object`.
        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.
        If the ``embed`` parameter is provided, it must be of type :class:`Embed` and
        it must be a rich embed type.
        Parameters
        ------------
        destination
            The location to send the message.
        content
            The content of the message to send. If this is missing,
            then the ``embed`` parameter must be present.
        tts : bool
            Indicates if the message should be sent using text-to-speech.
        embed: :class:`Embed`
            The rich embed for the content.
        Raises
        --------
        HTTPException
            Sending the message failed.
        Forbidden
            You do not have the proper permissions to send the message.
        NotFound
            The destination was not found and hence is invalid.
        InvalidArgument
            The destination parameter is invalid.
        Examples
        ----------
        Sending a regular message:
        .. code-block:: python
            await client.send_message(message.channel, 'Hello')
        Sending a TTS message:
        .. code-block:: python
            await client.send_message(message.channel, 'Goodbye.', tts=True)
        Sending an embed message:
        .. code-block:: python
            em = discord.Embed(title='My Embed Title', description='My Embed Content.', colour=0xDEADBF)
            em.set_author(name='Someone', icon_url=client.user.default_avatar_url)
            await client.send_message(message.channel, embed=em)
        Returns
        ---------
        :class:`Message`
            The message that was sent.
        """

        channel_id, guild_id = await self._resolve_destination(destination)

        if content:
            content = str(content)
            if len(content) > 2000:
                truncate_msg = '**... (truncated)**'
                rmatch = len(re.findall('```', content))
                if rmatch % 2 != 0: # odd number
                    truncate_msg = '```' + truncate_msg
                content = content[:2000 - len(truncate_msg)] + truncate_msg
        else:
            content = None

        if embed:
            embed = embed.to_dict()

        try:
            data = await self.http.send_message(channel_id, content, guild_id=guild_id, tts=tts, embed=embed)
            channel = self.get_channel(data.get('channel_id'))
            message = self.connection._create_message(channel=channel, **data)
            return message
        except discord.Forbidden as e:
            if embed: # let's try non embed
                e_text = '```md\n'
                for kv in embed.to_dict()['fields']:
                    e_text += kv['name'] + '\n-----------------------------------\n' + kv['value'] + '\n\n'
                e_text += '⚠ I need Attach Files permission (to send embeds)! ⚠'
                e_text += '```'
                data = await self.http.send_message(channel_id, content + '\n' + e_text, guild_id=guild_id, tts=tts, embed=None)
                channel = self.get_channel(data.get('channel_id'))
                message = self.connection._create_message(channel=channel, **data)
                return message
            else:
                raise e # didn't mean to catch that

    async def send_cmd_help(self, ctx):
        """Send command help for a command or subcommand."""
        if ctx.invoked_subcommand:
            pages = self.formatter.format_help_for(ctx, ctx.invoked_subcommand)
            for page in pages:
                await self.csend(ctx, page)
        else:
            pages = self.formatter.format_help_for(ctx, ctx.command)
            for page in pages:
                await self.csend(ctx, page)

    async def get_info(self):
        """Get bot info in an OrderedDict. To be implemented."""
        return None

    async def get_ram(self):
        """Get the bot's RAM usage info."""
        raw_musage = 0
        got_conversion = False
        musage_dec = 0
        musage_hex = 0
        if sys.platform.startswith('linux'): # Linux & Windows report in kilobytes
            raw_musage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            got_conversion = True
            musage_dec = raw_musage / 1000
            musage_hex = raw_musage / 1024
        elif sys.platform == 'darwin': # Mac reports in bytes
            raw_musage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            got_conversion = True
            musage_dec = raw_musage / 1000000 # 1 million. 1000 * 1000
            musage_hex = raw_musage / 1048576 # 1024 * 1024
        if got_conversion:
            return (got_conversion, musage_dec, musage_hex)
        else:
            return (got_conversion, 0) # to force tuple

    async def update_emote_data(self):
        """Fetch Twitch and FrakerFaceZ emote mappings."""
        with open(os.path.join(cur_dir, 'assets', 'emotes_twitch_global.json')) as f:
            twitch_global = json.loads(f.read())['emotes']
        with open(os.path.join(cur_dir, 'assets', 'emotes_twitch_subscriber.json')) as f:
            twitch_subscriber = json.loads(f.read())
        self.emotes['twitch'] = {**twitch_global, **twitch_subscriber}
        with open(os.path.join(cur_dir, 'assets', 'emotes_ffz.json')) as f:
            self.emotes['ffz'] = json.loads(f.read())
        with open(os.path.join(cur_dir, 'assets', 'emotes_bttv.json')) as f:
            raw_json = json.loads(f.read())
            bttv_v1 = {n: 'https:' + raw_json[n] for n in raw_json}
        with open(os.path.join(cur_dir, 'assets', 'emotes_bttv_2.json')) as f:
            raw_json2 = json.loads(f.read())
            bttv_v2 = {n: 'https://cdn.betterttv.net/emote/' + str(raw_json2[n]) + '/1x' for n in raw_json2}
        self.emotes['bttv'] = {**bttv_v1, **bttv_v2}
