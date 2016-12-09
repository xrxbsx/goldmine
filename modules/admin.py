"""Definition of the bot's Admin module.'"""
from __future__ import print_function
import asyncio
import random
import subprocess
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from util.perms import echeck_perms, check_perms
import util.datastore as store
from .cog import Cog

class Admin(Cog):
    """Commands useful for admins and/or moderators.
    Can be extremely powerful, use with caution!
    """

    def is_me(self, mem):
        """Checks if author of a message is this bot."""
        return mem.author == self.bot.user

    @commands.command(pass_context=True)
    async def purge(self, ctx):
        """Removes all of this bot's messages on a channel.
        Syntax: purge"""
        await echeck_perms(ctx, ['server_admin'])
        deleted = await self.bot.purge_from(ctx.message.channel, limit=500, check=self.is_me)
        await self.bot.send_message(ctx.message.channel, 'Deleted {} message(s)'.format(len(deleted)))

    @commands.command(pass_context=True)
    async def nuke(self, ctx):
        """NUKES a channel by deleting all messages!
        Syntax: nuke"""
        await echeck_perms(ctx, ['server_admin'])
        deleted = await self.bot.purge_from(ctx.message.channel, limit=1300)
        await self.bot.send_message(ctx.message.channel, 'Deleted {} message(s)'.format(len(deleted)))

    @commands.command(pass_context=True)
    async def update(self, ctx):
        """Auto-updates this bot and restarts if any code was updated.
        Syntax: update"""
        await echeck_perms(ctx, ['bot_owner'])
        await self.bot.say('Trying to update...')
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
            await self.bot.say('Bot was already up-to-date, not restarting.')
        else:
            await self.bot.say('Bot was able to update, now restarting.')
            await self.restart.invoke(ctx)

    @commands.command(pass_context=True)
    async def restart(self, ctx):
        """Restarts this bot.
        Syntax: restart"""
        await echeck_perms(ctx, ['bot_admin'])
#        for i in self.bot.servers:
#            await self.bot.send_message(i.default_channel, 'This bot (' + self.bname + ') is now restarting!')
        await self.bot.say('This bot is now restarting! Hopefully I come back alive :)')
        self.logger.info('This bot is now restarting!')
        self.bot.is_restart = True
#        await self.bot.logout() # Comment for people to not see that the bot restarted (to trick uptime)
        self.loop.stop()

    @commands.command(pass_context=True, hidden=True)
    async def eref(self, ctx, *rawtxt: str):
        """Evaluate some code in command scope.
        Syntax: eref [string to reference]"""
        await echeck_perms(ctx, ['bot_owner'])
        try:
            ev_output = eval(' '.join(rawtxt))
        except Exception as e:
            ev_output = 'An exception of type %s has occured!\n' % type(e).__name__ + str(e)
        await self.bot.say('```python\n' + str(ev_output) + '```')
    @commands.command(pass_context=True, hidden=True)
    async def seref(self, ctx, *rawtxt: str):
        """Evaluate a statement in command scope.
        Syntax:s eref [string to reference]"""
        await echeck_perms(ctx, ['bot_owner'])
        try:
            ev_output = exec(' '.join(rawtxt))
        except Exception as e:
            ev_output = 'An exception of type %s has occured!\n' % type(e).__name__ + str(e)
        await self.bot.say('```python\n' + str(ev_output) + '```')

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
    async def addadmin(self, ctx, target: discord.Member):
        """Add a user to the bot admin list.
        Syntax: addadmin [user]"""
        tmp = await check_perms(ctx, ['bot_admin'])
        if tmp:
            aentry = target.id
            rstore = await store.dump()
            if aentry not in rstore['bot_admins']:
                rstore['bot_admins'].extend([aentry])
                await store.write(rstore)
                await self.bot.say('The user specified has successfully been added to the bot admin list!')
            else:
                await self.bot.say('The user specified is already a bot admin!')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin, so you may not add others as admins!')

    @commands.command(pass_context=True, aliases=['deladmin', 'admindel', 'adminrm'])
    async def rmadmin(self, ctx, target: discord.Member):
        """Remove a user from the bot admin list.
        Syntax: rmadmin [user]"""
        tmp = await check_perms(ctx, ['bot_admin'])
        if tmp:
            aentry = target.id
            rstore = await store.dump()
            try:
                del rstore['bot_admins'][rstore['bot_admins'].index(aentry)]
                await store.write(rstore)
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
        rstore = await store.dump()
        alist = ''
        for i in rstore['bot_admins']:
            _name = ctx.message.server.get_member(i)
            if _name:
                alist += '**' + str(_name) + '**\n'
            else:
                _name = '**User not in current server! ID:** *{0}*\n'.format(i)
                alist += _name
        await self.bot.say('The following people are bot admins:\n' + alist)

    @commands.command(pass_context=True)
    async def getprop(self, ctx, pname: str):
        """Fetch a property from the datastore.
        Syntax: getprop [property name]"""
        pout = await store.get_prop(ctx.message, pname)
        await self.bot.say(pout)

    @commands.command(pass_context=True)
    async def setprop(self, ctx, pname: str, *values: str):
        """Set the value of a property on server level.
        Syntax: setprop [property name] [value]"""
        await echeck_perms(ctx, ['server_admin'])
        value = ' '.join(values)
        await store.set_prop(ctx.message, 'by_server', pname, value)
        await self.bot.say('Successfully set `{0}` as `{1}`!'.format(pname, value))
        if pname == 'bot_name':
            await self.bot.change_nickname(ctx.message.server.me, value)

    @commands.command(pass_context=True, aliases=['getprefix', 'setprefix'])
    async def prefix(self, ctx, *prefix):
        """Get or set the command prefix.
        Syntax: prefix {optional: new prefix}"""
        if prefix:
            await echeck_perms(ctx, ['server_admin'])
            jprefix = ' '.join(list(prefix))
            await store.set_prop(ctx.message, 'by_server', 'command_prefix', jprefix)
            await self.bot.say('Successfully set command prefix as `' + jprefix + '`!')
        else:
            oprefix = await store.get_cmdfix(ctx.message)
            await self.bot.say('**Current server command prefix is: **`' + oprefix + '`')

    @commands.command(pass_context=True, aliases=['usersetprop', 'psetprop'])
    async def usetprop(self, ctx, pname: str, value: str):
        """Set the value of a property on user level.
        Syntax: setprop [property name] [value]"""
        await store.set_prop(ctx.message, 'by_user', pname, value)
        await self.bot.say('Successfully set `{0}` as `{1}` for {2.mention}!'.format(pname, value, ctx.message.author))

    @commands.command(pass_context=True, aliases=['rsetprop'])
    async def rawsetprop(self, ctx, scope: str, pname: str, value: str):
        """Set the value of a property on any level.
        Syntax: rawsetprop [scope] [property name] [value]"""
        await echeck_perms(ctx, ['bot_admin'])
        await store.set_prop(ctx.message, scope, pname, value)
        await self.bot.say('Successfully set `{0}` as `{1}`!'.format(pname, value))

    @commands.command(pass_context=True)
    async def suspend(self, ctx):
        """Temporarily suspend the bot's command and conversation features.
        Syntax: suspend'"""
        await echeck_perms(ctx, ['bot_owner'])
        await self.bot.suspend()
        await self.bot.say('Successfully **suspended** the bot\'s command and conversation processing!')
