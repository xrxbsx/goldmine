"""Definition of the bot's Admin module.'"""
from __future__ import print_function
from contextlib import suppress
from importlib import import_module as imp
from datetime import datetime, timedelta
from util.perms import or_check_perms, echeck_perms, check_perms
from util.func import bdel, DiscordFuncs, _set_var, _import, _del_var, snowtime, assert_msg, check
from util.const import muted_perms
import util.dynaimport as di
from .cog import Cog

for mod in ['asyncio', 'random', 'functools', 'zipfile', 'io', 'copy', 'subprocess',
            'aiohttp', 'async_timeout', 'discord']:
    globals()[mod] = di.load(mod)
commands = di.load('util.commands')

def gimport(mod_name, name=None, attr=None):
    return exec(_import(mod_name, var_name=name, attr_name=attr))
setvar = lambda v, e: exec(_set_var(v, e))
delvar = lambda v: exec(_del_var(v))

class Admin(Cog):
    """Commands useful for admins and/or moderators.
    Can be extremely powerful, use with caution!
    """

    def __init__(self, bot):
        self.dc_funcs = DiscordFuncs(bot)
        super().__init__(bot)

    @commands.command(pass_context=True, aliases=['clear', 'purge', 'prune', 'clean'], no_pm=True)
    async def nuke(self, ctx, *count):
        """NUKES a channel by deleting all messages!
        Usage: nuke"""
        if self.bot.selfbot:
            await self.bot.say('**That command doesn\'t work in selfbot mode, due to a Discord restriction.**')
            return
        await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages'])
        mode = 'count'
        detected = False
        if not count:
            limit = 1500
            detected = True
        elif len(count) == 1:
            if count[0] == 'infinite':
                limit = 1750
                detected = True
            else:
                try:
                    limit = int(count[0]) + 1
                    if limit > 1751:
                        await self.bot.say(ctx.message.author.mention + ' **You can only clean messages by user or 1-1750!**')
                        return
                    detected = True
                except ValueError:
                    pass
        if not detected:
            mode = 'target'
            targets = set()
            members = {}
            s = ctx.message.server
            for i in getattr(s, 'members', []):
                members[i.mention] = i
                members[i.id] = i
                members[i.display_name] = i
                members[i.name] = i
            for i in count:
                try:
                    member = s.get_member(i)
                except AttributeError:
                    try:
                        member = await self.bot.get_user_info(i)
                    except discord.HTTPException:
                        member = None
                if member:
                    targets.add(member)
                else:
                    try:
                        member = await self.bot.get_user_info(i)
                    except discord.HTTPException:
                        member = None
                    if member:
                        targets.add(member)
            names = []
            _i = 0
            while _i < len(count):
                names.append(count[_i])
                with suppress(KeyError):
                    if ' '.join(names) in members:
                        targets.add(members[' '.join(names)])
                        names = []
                    elif _i + 1 == len(count):
                        targets.add(members[count[0]])
                        _i = -1
                        users = count[1:]
                        names = []
                _i += 1
            if not targets:
                await self.bot.say('**No matching users, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!**')
                return
            purge_ids = [m.id for m in targets]
        try:
            if mode == 'count':
                deleted = await self.bot.purge_from(ctx.message.channel, limit=limit)
            else:
                deleted = await self.bot.purge_from(ctx.message.channel, limit=1500, check=lambda m: m.author.id in purge_ids)
        except discord.Forbidden:
            await self.bot.say(ctx.message.author.mention + ' **I don\'t have enough permissions to do that here 😢**')
            return
        dn = len(deleted)
        del_msg = await self.bot.say('👏 I\'ve finished, deleting {0} message{1}!'.format(dn, ('' if dn == 1 else 's')))
        await asyncio.sleep(2.8)
        await self.bot.delete_message(del_msg)

    @commands.command(pass_context=True, aliases=['rawupdate', 'rupdate'])
    async def update(self, ctx):
        """Auto-updates this bot and restarts if any code was updated.
        Usage: update"""
        await echeck_perms(ctx, ['bot_owner'])
        restart = not ctx.invoked_with.startswith('r')
        msg = await self.bot.say('Trying to update...')
        r_key = ', now restarting' if restart else ''
        r_not_key = ', not restarting' if restart else ''
#        subprocess.check_output(['git', 'reset', 'HEAD', '--hard'])
        dest = ctx.message.channel if self.bot.selfbot else ctx.message.author
        try:
            gitout = await self.loop.run_in_executor(None, functools.partial(subprocess.check_output, ['git', 'pull'], stderr=subprocess.STDOUT))
            gitout = gitout.decode('utf-8')
        except subprocess.CalledProcessError as exp:
            await self.bot.edit_message(msg, 'An error occured while attempting to update!')
            await self.bot.send_message(dest, '```' + str(exp) + '```')
            gitout = False
        '''async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(15): # for streaming
                async with session.get('https://github.com/Armored-Dragon/goldmine/archive/master.zip') as r:
                    tarball = await r.read()
        with zipfile.ZipFile(io.BytesIO(tarball)) as z:
            z.extractall(self.bot.dir)'''
        if gitout != False:
            await self.bot.send_message(dest, 'Update Output:\n```' + gitout + '```')
        if not gitout:
            await self.bot.edit_message(msg, msg.content + f'\nUpdate failed{r_not_key}.')
        elif gitout.split('\n')[-2:][0] == 'Already up-to-date.':
            await self.bot.edit_message(msg, f'Bot was already up-to-date{r_not_key}.')
        else:
            await self.bot.edit_message(msg, f'Bot was able to update{r_key}.')
        if restart:
            await self.restart.invoke(ctx)

    @commands.command(pass_context=True)
    async def restart(self, ctx):
        """Restarts this bot.
        Usage: restart"""
        await echeck_perms(ctx, ['bot_owner'])
#        for i in self.bot.servers:
#            await self.bot.send_message(i.default_channel, 'This bot (' + self.bname + ') is now restarting!')
        self.bot.store_writer.cancel()
        await self.store.commit()
        if ctx.invoked_with != 'update':
            await self.bot.say('I\'ll try to restart. Hopefully I come back alive :stuck_out_tongue:')
        self.logger.info('The bot is now restarting!')
        self.bot.is_restart = True
#        await self.bot.logout() # Comment for people to not see that the bot restarted (to trick uptime)
        self.loop.stop()

    @commands.command(pass_context=True, aliases=['dwrite', 'storecommit', 'commitstore', 'commit_store', 'write_store'], hidden=True)
    async def dcommit(self, ctx):
        """Commit the current datastore.
        Usage: dcommit"""
        await echeck_perms(ctx, ['bot_owner'])
        await self.store.commit()
        await self.bot.say('**Commited the current copy of the datastore!**')

    @commands.command(pass_context=True, aliases=['dread', 'storeread', 'readstore', 'load_store', 'read_store'], hidden=True)
    async def dload(self, ctx):
        """Load the datastore from disk. POTENTIALLY DESTRUCTIVE!
        Usage: dload"""
        await echeck_perms(ctx, ['bot_owner'])
        await self.bot.say('**ARE YOU SURE YOU WANT TO LOAD THE DATASTORE?** *yes, no*')
        resp = await self.bot.wait_for_message(author=ctx.message.author)
        if resp.content.lower() == 'yes':
            await self.store.commit()
            await self.bot.say('**Read the datastore from disk, overwriting current copy!**')
        else:
            await self.bot.say('**Didn\'t say yes, aborting.**')

    @commands.cooldown(1, 16, type=commands.BucketType.default)
    @commands.command(pass_context=True)
    async def broadcast(self, ctx, *, text: str):
        """Broadcast a message to all servers.
        Usage: broadcast [message]"""
        await echeck_perms(ctx, ['bot_owner'])
        err = ''
        for i in self.bot.servers:
            try:
                await self.bot.send_message(i.default_channel, text)
            except discord.Forbidden:
                satisfied = False
                c_count = 0
                try_channels = list(i.channels)
                channel_count = len(try_channels) - 1
                while not satisfied:
                    with suppress(discord.Forbidden, discord.HTTPException):
                        await self.bot.send_message(try_channels[c_count], text)
                        satisfied = True
                    if c_count >= channel_count:
                        err += f'`[WARN]` Couldn\'t broadcast to server **{i.name}**\n'
                        satisfied = True
                    c_count += 1
        if err:
            await self.bot.say(err)

    @commands.command(pass_context=True, hidden=True, aliases=['pyeval', 'rxeval', 'reref', 'xeval'])
    async def eref(self, ctx, *, code: str):
        """Evaluate some code in command scope.
        Usage: eref [code to execute]"""
        await echeck_perms(ctx, ['bot_owner'])
        dc = self.dc_funcs
        def print(*ina: str):
            self.loop.create_task(self.bot.say(' '.join(ina)))
            return True
        try:
            ev_output = eval(bdel(bdel(code, '```python'), '```py').strip('`'))
        except Exception as e:
            ev_output = 'An exception of type %s occured!\n' % type(e).__name__ + str(e)
        o = str(ev_output)
        if ev_output is None:
            await self.bot.say('✅')
            return
        if ctx.invoked_with.startswith('r'):
            await self.bot.say(o)
        else:
            await self.bot.say('```py\n' + o + '```')
    @commands.command(pass_context=True, hidden=True, aliases=['rseref', 'meref', 'rmeref'])
    async def seref(self, ctx, *, code: str):
        """Evaluate some code (multi-statement) in command scope.
        Usage: seref [code to execute]"""
        await echeck_perms(ctx, ['bot_owner'])
        dc = self.dc_funcs
        def print(*ina: str):
            self.loop.create_task(self.bot.say(' '.join(ina)))
            return True
        try:
            ev_output = exec(bdel(bdel(code, '```python'), '```py').strip('`'))
        except Exception as e:
            ev_output = 'An exception of type %s occured!\n' % type(e).__name__ + str(e)
        o = str(ev_output)
        if ev_output is None:
            await self.bot.say('✅')
            return
        if ctx.invoked_with.startswith('r'):
            await self.bot.say(o)
        else:
            await self.bot.say('```py\n' + o + '```')

    @commands.command(pass_context=True, aliases=['amiadmin', 'isadmin', 'admin'])
    async def admintest(self, ctx):
        """Check to see if you're registered as a bot admin.
        Usage: admintest'"""
        tmp = await check_perms(ctx, ['bot_admin'])
        if tmp:
            await self.bot.say(ctx.message.author.mention + ' You are a bot admin! :smiley:')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin! :slight_frown:')

    @commands.command(pass_context=True, aliases=['adminadd'])
    async def addadmin(self, ctx, *rrtarget: str):
        """Add a user to the bot admin list.
        Usage: addadmin [user]"""
        tmp = await check_perms(ctx, ['bot_admin'])
        if not rrtarget:
            await self.bot.say('**You need to specify a name, nickname, name#0000, mention, or ID!**')
            return
        rtarget = ' '.join(rrtarget)
        try:
            _target = ctx.message.server.get_member_named(rtarget)
        except AttributeError:
            _target = None
        if _target:
            target = _target.id
        elif len(rtarget) == 18:
            target = rrtarget[0]
        elif ctx.message.mentions:
            target = ctx.message.mentions[0].id
        else:
            await self.bot.say('**Invalid name! Name, nickname, name#0000, mention, or ID work.**')
            return
        if tmp:
            aentry = target
            if aentry not in self.dstore['bot_admins']:
                self.dstore['bot_admins'].append(aentry)
                await self.bot.say('The user specified has successfully been added to the bot admin list!')
            else:
                await self.bot.say('The user specified is already a bot admin!')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin, so you may not add others as admins!')

    @commands.command(pass_context=True, aliases=['deladmin', 'admindel', 'adminrm'])
    async def rmadmin(self, ctx, *rrtarget: str):
        """Remove a user from the bot admin list.
        Usage: rmadmin [user]"""
        tmp = await check_perms(ctx, ['bot_admin'])
        if not rrtarget:
            await self.bot.say('**You need to specify a name, nickname, name#discriminator, or ID!**')
            return
        rtarget = ' '.join(rrtarget)
        try:
            _target = ctx.message.server.get_member_named(rtarget)
        except AttributeError:
            _target = None
        if _target:
            target = _target.id
        elif len(rtarget) in [15, 16, 17, 18, 19, 20]:
            target = rrtarget[0]
        else:
            await self.bot.say('**Invalid name! Name, nickname, name#discriminator, or ID work.**')
            return
        if tmp:
            aentry = target
            try:
                self.dstore['bot_admins'].remove(aentry)
            except ValueError:
                await self.bot.say('The user specified is not a bot admin!')
            else:
                await self.bot.say('The user specified has successfully been demoted!')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin, so you may not demote other admins!')

    @commands.command(pass_context=True, aliases=['admins'])
    async def adminlist(self, ctx):
        """List all bot admins defined.
        Usage: adminlist"""
        alist = ''
        for i in self.dstore['bot_admins']:
            nid = ''
            try:
                _name = ctx.message.server.get_member(i)
            except AttributeError:
                _name = None
            if not _name:
                try:
                    _name = await self.bot.get_user_info(i)
                except discord.NotFound:
                    _name = 'UNKNOWN'
                    nid = i
            if not nid:
                nid = _name.id
            alist += '**' + str(_name) + f'** (ID `{nid}`)\n'
        await self.bot.say('The following people are bot admins:\n' + alist)

    @commands.command(pass_context=True)
    async def getprop(self, ctx, pname: str):
        """Fetch a property from the datastore.
        Usage: getprop [property name]"""
        try:
            pout = await self.store.get_prop(ctx.message, pname)
        except Exception:
            await self.bot.say('⚠ An error occured.')
            return
        await self.bot.say(pout)

    @commands.command(pass_context=True, no_pm=True)
    async def setprop(self, ctx, pname: str, *values: str):
        """Set the value of a property on server level.
        Usage: setprop [property name] [value]"""
        await echeck_perms(ctx, ['manage_server'])
        value = ' '.join(values)
        await self.store.set_prop(ctx.message, 'by_server', pname, value)
        await self.bot.say('Successfully set `{0}` as `{1}`!'.format(pname, value))
        if pname == 'bot_name':
            await self.bot.change_nickname(ctx.message.server.me, value)

    @commands.command(pass_context=True, aliases=['getprefix', 'setprefix'])
    async def prefix(self, ctx, *prefix: str):
        """Get or set the command prefix.
        Usage: prefix {new prefix}"""
        sk = ' server'
        prop = ('by_server', 'command_prefix')
        if self.bot.selfbot:
            sk = ''
            prop = ('global', 'selfbot_prefix')
        if prefix:
            await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages'])
            jprefix = ' '.join(list(prefix))
            await self.store.set_prop(ctx.message, *prop, jprefix)
            await self.bot.say('Successfully set command prefix as `' + jprefix + '`!')
        else:
            oprefix = await self.store.get_cmdfix(ctx.message)
            await self.bot.say(f'**Current{sk} command prefix is: **`' + oprefix + '`')

    @commands.command(pass_context=True, aliases=['usersetprop', 'psetprop'])
    async def usetprop(self, ctx, pname: str, value: str):
        """Set the value of a property on user level.
        Usage: setprop [property name] [value]"""
        await self.store.set_prop(ctx.message, 'by_user', pname, value)
        await self.bot.say('Successfully set `{0}` as `{1}` for {2.mention}!'.format(pname, value, ctx.message.author))

    @commands.command(pass_context=True, aliases=['rsetprop'])
    async def rawsetprop(self, ctx, scope: str, pname: str, value: str):
        """Set the value of a property on any level.
        Usage: rawsetprop [scope] [property name] [value]"""
        await echeck_perms(ctx, ['bot_admin'])
        try:
            await self.store.set_prop(ctx.message, scope, pname, value)
        except Exception:
            await self.bot.say('⚠ An error occured.')
            return
        await self.bot.say('Successfully set `{0}` as `{1}`!'.format(pname, value))

    @commands.command(pass_context=True)
    async def suspend(self, ctx):
        """Bring the bot offline (in a resumable state).
        Usage: suspend'"""
        await echeck_perms(ctx, ['bot_owner'])
        await self.bot.suspend()
        await self.bot.say('Successfully **suspended** me! (I should now be offline.)\nI will still count experience points.')
    @commands.command(pass_context=True, aliases=['ssuspend'])
    async def ususpend(self, ctx):
        """Temporarily suspend the bot's command and conversation features.
        Usage: suspend'"""
        await echeck_perms(ctx, ['bot_owner'])
        self.bot.status = 'invisible'
        await self.bot.say('Successfully **suspended** my message processing! (I should stay online.)\nI will still count experience points.')

    @commands.command(pass_context=True, hidden=True, aliases=['slist'])
    async def serverlist(self, ctx):
        """List the servers I am in.
        Usage: serverlist"""
        await echeck_perms(ctx, ['bot_owner'])
        pager = commands.Paginator()
        for server in self.bot.servers:
            pager.add_line(server.name)
        for page in pager.pages:
            await self.bot.say(page)

    @commands.command(pass_context=True, hidden=True, aliases=['treelist', 'stree', 'treeservers', 'trees', 'tservers'])
    async def servertree(self, ctx, *ids: str):
        """List the servers I am in (tree version).
        Usage: servertree"""
        await echeck_perms(ctx, ['bot_owner'])
        pager = commands.Paginator(prefix='```diff')
        servers: List[discord.Server]
        if ids:
            s_map = {i.id: i for i in self.bot.servers}
            for sid in ids:
                with assert_msg(ctx, '**ID** `%s` **is invalid. (must be 18 numbers)**' % sid):
                    check(len(sid) == 18)
                try:
                    servers.append(s_map[sid])
                except KeyError:
                    await self.bot.say('Server ID **%s** not found.' % sid)
                    return False
        else:
            servers = self.bot.servers
        for server in servers:
            pager.add_line('+ ' + server.name + ' [{0} members] [ID {1}]'.format(str(len(server.members)), server.id))
            for channel in server.channels:
                xname = channel.name
                if str(channel.type) == 'voice':
                    xname = '[voice] ' + xname
                pager.add_line('  • ' + xname)
        for page in pager.pages:
            await self.bot.say(page)

    @commands.command(pass_context=True, hidden=True, aliases=['mlist', 'listmembers'])
    async def memberlist(self, ctx, *server_ids: str):
        """List the members of a server.
        Usage: memberlist [server ids]"""
        await echeck_perms(ctx, ['bot_owner'])
        if not server_ids:
            await self.bot.say('**You need to specify at least 1 server ID!**')
            return False
        pager = commands.Paginator(prefix='```diff')
        pager.add_line('< -- SERVERS <-> MEMBERS -- >')
        server_table = {i.id: i for i in self.bot.servers}
        for sid in server_ids:
            with assert_msg(ctx, f'**ID** `{sid}` **is invalid. (must be 18 numbers)**'):
                check(len(sid) == 18)
            try:
                server = server_table[sid]
            except KeyError:
                await self.bot.say(f'**ID** `{sid}` **was not found.**')
                return False
            pager.add_line('+ ' + server.name + ' [{0} members] [ID {1}]'.format(str(len(server.members)), server.id))
            for member in server.members:
                pager.add_line('- ' + str(member))
        for page in pager.pages:
            await self.bot.say(page)

    async def progress(self, msg: discord.Message, begin_txt: str):
        """Play loading animation with dots and moon."""
        fmt = '{0}{1} {2}'
        anim = '🌑🌒🌓🌔🌕🌝🌖🌗🌘🌚'
        anim_len = len(anim) - 1
        anim_i = 0
        dot_i = 1
        while True:
            await self.bot.edit_message(msg, fmt.format(begin_txt, ('.' * dot_i) + ' ' * (3 - dot_i), anim[anim_i]))
            dot_i += 1
            if dot_i > 3:
                dot_i = 1
            anim_i += 1
            if anim_i > anim_len:
                anim_i = 0
            await asyncio.sleep(1.1)

    @commands.command(pass_context=True)
    async def mute(self, ctx, *, member: discord.Member):
        """Mute someone on voice and text chat.
        Usage: mute [person's name]"""
        await or_check_perms(ctx, ['mute_members', 'manage_roles', 'manage_channels', 'manage_messages'])
        status = await self.bot.say('Muting... 🌚')
        pg_task = self.loop.create_task(self.progress(status, 'Muting'))
        try:
            ch_perms = discord.PermissionOverwrite(**{p: False for p in muted_perms})
            for channel in ctx.message.server.channels:
                await self.bot.edit_channel_permissions(channel, member, ch_perms)
            await self.bot.server_voice_state(member, mute=True, deafen=None)
            pg_task.cancel()
            await self.bot.delete_message(status)
            await self.bot.say('Successfully muted **%s**!' % str(member))
        except (discord.Forbidden, discord.HTTPException):
            pg_task.cancel()
            await self.bot.delete_message(status)
            await self.bot.say('**I don\'t have enough permissions to do that!**')

    @commands.command(pass_context=True)
    async def unmute(self, ctx, *, member: discord.Member):
        """Unmute someone on voice and text chat.
        Usage: unmute [person's name]"""
        await or_check_perms(ctx, ['mute_members', 'manage_roles', 'manage_channels', 'manage_messages'])
        status = await self.bot.say('Unmuting... 🌚')
        pg_task = self.loop.create_task(self.progress(status, 'Unmuting'))
        role_map = {r.name: r for r in member.roles}
        try:
            if 'Muted' in role_map:
                await self.bot.remove_roles(member, role_map['Muted'])
            ch_perms = discord.PermissionOverwrite(**{p: None for p in muted_perms})
            for channel in ctx.message.server.channels:
                await self.bot.edit_channel_permissions(channel, member, ch_perms)
            await self.bot.server_voice_state(member, mute=False, deafen=None)
            pg_task.cancel()
            await self.bot.delete_message(status)
            await self.bot.say('Successfully unmuted **%s**!' % str(member))
        except (discord.Forbidden, discord.HTTPException):
            pg_task.cancel()
            await self.bot.delete_message(status)
            await self.bot.say('**I don\'t have enough permissions to do that!**')

    @commands.command(pass_context=True, aliases=['sf', 'sendf', 'filesend', 'fs'])
    async def sendfile(self, ctx, path: str = 'assets/soon.gif', msg: str = '📧 File incoming! 📧'):
        """Send a file to Discord.
        Usage: sendfile [file path] {message}"""
        await echeck_perms(ctx, ['bot_owner'])
        with open(path, 'rb') as f:
            await self.bot.send_file(ctx.message.channel, fp=f, content=msg)

    @commands.command(pass_context=True, hidden=True)
    async def repeat(ctx, times : int, *, command: str):
        """Repeats a command a specified number of times.
        Usage: repeat [times] [command]"""
        msg = copy.copy(ctx.message)
        msg.content = command
        for i in range(times):
            await self.bot.process_commands(msg)

    @commands.command(pass_context=True)
    async def console_msg(self, ctx):
        await echeck_perms(ctx, ['bot_owner'])
        def console_task(ch):
            while True:
                text_in = input('Message> ')
                if text_in == 'quit':
                    return
                else:
                    self.loop.create_task(self.bot.send_message(ch, text_in))
        await self.bot.say('Now entering: Console message mode')
        print('Type \'quit\' to exit.')
        await self.loop.run_in_executor(None, console_task, ctx.message.channel)
        await self.bot.say('Exited console message mode')

def setup(bot):
    c = Admin(bot)
    bot.add_cog(c)
