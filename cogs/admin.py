"""Definition of the bot's Admin module.'"""
from __future__ import print_function
import asyncio
import random
import subprocess
from importlib import import_module as imp
from datetime import datetime, timedelta

import discord
import util.commands as commands
from util.perms import or_check_perms, echeck_perms, check_perms
from util.func import bdel, DiscordFuncs, _set_var, _import, _del_var, snowtime
from .cog import Cog


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

    @commands.command(pass_context=True)
    async def purge(self, ctx):
        """Removes all of this bot's messages on a channel.
        Syntax: purge"""
        await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages'])
        deleted = await self.bot.purge_from(ctx.message.channel, limit=500, check=lambda m: m == self.bot.user)
        await self.bot.say('Deleted {} message(s)'.format(len(deleted)))

    @commands.command(pass_context=True)
    async def nuke(self, ctx):
        """NUKES a channel by deleting all messages!
        Syntax: nuke"""
        await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages'])
        deleted = await self.bot.purge_from(ctx.message.channel, limit=1300)
        await self.bot.say('Deleted {} message(s)'.format(len(deleted)))

    @commands.command(pass_context=True)
    async def update(self, ctx):
        """Auto-updates this bot and restarts if any code was updated.
        Syntax: update"""
        await echeck_perms(ctx, ['bot_owner'])
        msg = await self.bot.say('Trying to update...')
#        subprocess.check_output(['git', 'reset', 'HEAD', '--hard'])
        try:
            gitout = subprocess.check_output(['git', 'pull', '-v'], stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as exp:
            await self.bot.say('An error occured while attempting to update!')
            await self.bot.send_message(ctx.message.author, '```' + str(exp) + '```')
            gitout = False
        if gitout != False:
            await self.bot.send_message(ctx.message.author, 'Update Output:\n```' + gitout + '```')
        if not gitout:
            await self.bot.say('Update failed, not restarting.')
        elif gitout.split('\n')[-2:][0] == 'Already up-to-date.':
            await self.bot.edit_message(msg, 'Bot was already up-to-date, not restarting.')
        else:
            await self.bot.edit_message(msg, 'Bot was able to update, now restarting.')
            await self.restart.invoke(ctx)

    @commands.command(pass_context=True)
    async def restart(self, ctx):
        """Restarts this bot.
        Syntax: restart"""
        await echeck_perms(ctx, ['bot_owner'])
#        for i in self.bot.servers:
#            await self.bot.send_message(i.default_channel, 'This bot (' + self.bname + ') is now restarting!')
        self.bot.store_writer.cancel()
        await self.bot.store.commit()
        if ctx.invoked_with != 'update':
            await self.bot.say('I\'ll try to restart. Hopefully I come back alive :stuck_out_tongue:')
        self.logger.info('The bot is now restarting!')
        self.bot.is_restart = True
#        await self.bot.logout() # Comment for people to not see that the bot restarted (to trick uptime)
        self.loop.stop()

    @commands.command(pass_context=True, aliases=['dwrite', 'storecommit', 'commitstore', 'commit_store', 'write_store'], hidden=True)
    async def dcommit(self, ctx):
        """Commit the current datastore.
        Syntax: dcommit"""
        await echeck_perms(ctx, ['bot_owner'])
        await self.bot.store.commit()
        await self.bot.say('**Commited the current copy of the datastore!**')

    @commands.command(pass_context=True, aliases=['dread', 'storeread', 'readstore', 'load_store', 'read_store'], hidden=True)
    async def dload(self, ctx):
        """Load the datastore from disk. POTENTIALLY DESTRUCTIVE!
        Syntax: dload"""
        await echeck_perms(ctx, ['bot_owner'])
        await self.bot.say('**ARE YOU SURE YOU WANT TO LOAD THE DATASTORE?** *yes, no*')
        resp = await self.bot.wait_for_message(author=ctx.message.author)
        if resp.content.lower() == 'yes':
            await self.bot.store.commit()
            await self.bot.say('**Read the datastore from disk, overwriting current copy!**')
        else:
            await self.bot.say('**Didn\'t say yes, aborting.**')

    @commands.cooldown(1, 16, type=commands.BucketType.default)
    @commands.command(pass_context=True)
    async def broadcast(self, ctx, filler_string: str):
        """Broadcast a message to all servers.
        Syntax: broadcast [message]"""
        await echeck_perms(ctx, ['bot_owner'])
        for i in self.bot.servers:
            try:
                await self.bot.send_message(i.default_channel, ctx.raw_args)
            except discord.Forbidden:
                satisfied = False
                c_count = 0
                try_channels = list(i.channels)
                channel_count = len(try_channels) - 1
                while not satisfied:
                    try:
                        await self.bot.send_message(try_channels[c_count], ctx.raw_args)
                        satisfied = True
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                    if c_count > channel_count:
                        await self.bot.say('`[WARN]` Couldn\'t broadcast to server **' + i.name + '**')
                        satisfied = True
                    c_count += 1

    @commands.command(pass_context=True, hidden=True, aliases=['pyeval', 'rxeval', 'reref', 'xeval'])
    async def eref(self, ctx, filler_string: str):
        """Evaluate some code in command scope.
        Syntax: eref [code to execute]"""
        await echeck_perms(ctx, ['bot_owner'])
        dc = self.dc_funcs
        def print(*ina: str):
            asyncio.ensure_future(self.bot.say(' '.join(ina)))
            return True
        try:
            ev_output = eval(bdel(bdel(ctx.raw_args, '```python'), '```py').strip('`'))
        except Exception as e:
            ev_output = 'An exception of type %s has occured!\n' % type(e).__name__ + str(e)
        o = str(ev_output)
        if ctx.invoked_with.startswith('r'):
            await self.bot.say(o)
        else:
            await self.bot.say('```py\n' + o + '```')
    @commands.command(pass_context=True, hidden=True, aliases=['rseref', 'meref', 'rmeref'])
    async def seref(self, ctx, filler_string: str):
        """Evaluate some code (multi-statement) in command scope.
        Syntax: seref [code to execute]"""
        await echeck_perms(ctx, ['bot_owner'])
        dc = self.dc_funcs
        def print(*ina: str):
            asyncio.ensure_future(self.bot.say(' '.join(ina)))
            return True
        try:
            ev_output = exec(bdel(bdel(ctx.raw_args, '```python'), '```py').strip('`'))
        except Exception as e:
            ev_output = 'An exception of type %s has occured!\n' % type(e).__name__ + str(e)
        o = str(ev_output)
        if ctx.invoked_with.startswith('r'):
            await self.bot.say(o)
        else:
            await self.bot.say('```py\n' + o + '```')

    @commands.command(pass_context=True, aliases=['amiadmin', 'isadmin', 'admin'])
    async def admintest(self, ctx):
        """Check to see if you're registered as a bot admin.
        Syntax: admintest'"""
        tmp = await check_perms(ctx, ['bot_admin'])
        if tmp:
            await self.bot.say(ctx.message.author.mention + ' You are a bot admin! :smiley:')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin! :slight_frown:')

    @commands.command(pass_context=True, aliases=['adminadd'])
    async def addadmin(self, ctx, *rrtarget: str):
        """Add a user to the bot admin list.
        Syntax: addadmin [user]"""
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
        elif len(rtarget) == 18:
            target = rtarget[0]
        else:
            await self.bot.say('**Invalid name! Name, nickname, name#discriminator, or ID work.**')
            return
        if tmp:
            aentry = target
            if aentry not in self.dstore['bot_admins']:
                self.dstore['bot_admins'].extend([aentry])
                await self.bot.say('The user specified has successfully been added to the bot admin list!')
            else:
                await self.bot.say('The user specified is already a bot admin!')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin, so you may not add others as admins!')

    @commands.command(pass_context=True, aliases=['deladmin', 'admindel', 'adminrm'])
    async def rmadmin(self, ctx, *rrtarget: str):
        """Remove a user from the bot admin list.
        Syntax: rmadmin [user]"""
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
        elif len(rtarget) == 18:
            target = rtarget[0]
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
        Syntax: adminlist"""
        alist = ''
        for i in self.dstore['bot_admins']:
            try:
                _name = ctx.message.server.get_member(i)
            except AttributeError:
                _name = None
            if not _name:
                _name = await self.bot.get_user_info(i)
            alist += '**' + str(_name) + '**\n'
        await self.bot.say('The following people are bot admins:\n' + alist)

    @commands.command(pass_context=True)
    async def getprop(self, ctx, pname: str):
        """Fetch a property from the datastore.
        Syntax: getprop [property name]"""
        pout = await self.store.get_prop(ctx.message, pname)
        await self.bot.say(pout)

    @commands.command(pass_context=True, no_pm=True)
    async def setprop(self, ctx, pname: str, *values: str):
        """Set the value of a property on server level.
        Syntax: setprop [property name] [value]"""
        await echeck_perms(ctx, ['manage_server'])
        value = ' '.join(values)
        await self.store.set_prop(ctx.message, 'by_server', pname, value)
        await self.bot.say('Successfully set `{0}` as `{1}`!'.format(pname, value))
        if pname == 'bot_name':
            await self.bot.change_nickname(ctx.message.server.me, value)

    @commands.command(pass_context=True, aliases=['getprefix', 'setprefix'])
    async def prefix(self, ctx, *prefix):
        """Get or set the command prefix.
        Syntax: prefix {optional: new prefix}"""
        if prefix:
            await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages'])
            jprefix = ' '.join(list(prefix))
            await self.store.set_prop(ctx.message, 'by_server', 'command_prefix', jprefix)
            await self.bot.say('Successfully set command prefix as `' + jprefix + '`!')
        else:
            oprefix = await self.store.get_cmdfix(ctx.message)
            await self.bot.say('**Current server command prefix is: **`' + oprefix + '`')

    @commands.command(pass_context=True, aliases=['usersetprop', 'psetprop'])
    async def usetprop(self, ctx, pname: str, value: str):
        """Set the value of a property on user level.
        Syntax: setprop [property name] [value]"""
        await self.store.set_prop(ctx.message, 'by_user', pname, value)
        await self.bot.say('Successfully set `{0}` as `{1}` for {2.mention}!'.format(pname, value, ctx.message.author))

    @commands.command(pass_context=True, aliases=['rsetprop'])
    async def rawsetprop(self, ctx, scope: str, pname: str, value: str):
        """Set the value of a property on any level.
        Syntax: rawsetprop [scope] [property name] [value]"""
        await echeck_perms(ctx, ['bot_admin'])
        await self.store.set_prop(ctx.message, scope, pname, value)
        await self.bot.say('Successfully set `{0}` as `{1}`!'.format(pname, value))

    @commands.command(pass_context=True)
    async def suspend(self, ctx):
        """Bring the bot offline (in a resumable state).
        Syntax: suspend'"""
        await echeck_perms(ctx, ['bot_owner'])
        await self.bot.suspend()
        await self.bot.say('Successfully **suspended** me! (I should now be offline.)\nI will still count experience points.')
    @commands.command(pass_context=True, aliases=['ssuspend'])
    async def ususpend(self, ctx):
        """Temporarily suspend the bot's command and conversation features.
        Syntax: suspend'"""
        await echeck_perms(ctx, ['bot_owner'])
        self.bot.status = 'invisible'
        await self.bot.say('Successfully **suspended** my message processing! (I should stay online.)\nI will still count experience points.')

    @commands.command(pass_context=True, hidden=True, aliases=['slist'])
    async def serverlist(self, ctx):
        """List the servers I am in.
        Syntax: serverlist"""
        await echeck_perms(ctx, ['bot_owner'])
        pager = commands.Paginator()
        for server in self.bot.servers:
            pager.add_line(server.name)
        for page in pager.pages:
            await self.bot.say(page)

    @commands.command(pass_context=True, hidden=True, aliases=['treelist', 'stree', 'treeservers', 'trees', 'tservers'])
    async def servertree(self, ctx, *ids):
        """List the servers I am in (tree version).
        Syntax: servertree"""
        await echeck_perms(ctx, ['bot_owner'])
        pager = commands.Paginator(prefix='```diff')
        servers = []
        if ids:
            s_map = {i.id: i for i in self.bot.servers}
            for sid in ids:
                try:
                    servers.append(s_map[sid])
                except KeyError:
                    await self.bot.say('Server ID **%s** not found.' % sid)
                    return
        else:
            servers = self.bot.servers
        for server in servers:
            pager.add_line('+ ' + server.name + ' [{0} members] [ID {1}]'.format(str(len(server.members)), server.id))
            for channel in server.channels:
                xname = channel.name
                if str(channel.type) == 'voice':
                    xname = '[voice] ' + xname
                pager.add_line('  - ' + xname)
        for page in pager.pages:
            await self.bot.say(page)

    @commands.command(pass_context=True, hidden=True, aliases=['mlist', 'listmembers'])
    async def memberlist(self, ctx, *server_ids: str):
        """List the members of a server.
        Syntax: memberlist [server ids]"""
        await echeck_perms(ctx, ['bot_owner'])
        if not server_ids:
            await self.bot.say('**You need to specify at least 1 server ID!**')
            return
        pager = commands.Paginator(prefix='```diff')
        pager.add_line('< -- SERVERS <-> MEMBERS -- >')
        server_table = {i.id: i for i in self.bot.servers}
        for sid in server_ids:
            try:
                server = server_table[sid]
            except KeyError:
                await self.bot.say('**ID** `%s` **was not found.**' % sid)
                return
            pager.add_line('+ ' + server.name + ' [{0} members] [ID {1}]'.format(str(len(server.members)), server.id))
            for member in server.members:
                pager.add_line('- ' + str(member))
        for page in pager.pages:
            await self.bot.say(page)

def setup(bot):
    c = Admin(bot)
    bot.add_cog(c)
