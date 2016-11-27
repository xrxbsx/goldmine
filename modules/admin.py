"""Definition of the bot's Admin module.'"""
from __future__ import print_function
import asyncio
import subprocess

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
        await echeck_perms(ctx, ['bot_admin'])
        await self.bot.say('Trying to update...')
        try:
            gitout = subprocess.check_output(['git', 'pull', '-v'], stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as exp:
            await self.bot.say('An error has occured while attempting to update!')
            await self.bot.say('```' + str(exp) + '```')
            await self.bot.say('Aborting. Contact Dragon5232 for help.')
            gitout = False
        if gitout != False:
            await self.bot.say('Output:\n```' + gitout + '```')
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
        print('This bot is now restarting!')
        self.bot.is_restart = True
        await self.bot.logout()
        self.loop.stop()

    @commands.command(pass_context=True, hidden=True)
    async def eref(self, ctx, *rawtxt: str):
        """Evaluate an object in command scope.
        Syntax: eref [string to reference]"""
        await echeck_perms(ctx, ['bot_admin'])
        rstore = await store.dump()
        await self.bot.say(str(eval(' '.join(rawtxt))))

    @commands.command(pass_context=True)
    async def admintest(self, ctx):
        """Check to see if you're registered as a bot admin.
        Syntax: admintest'"""
        tmp = await check_perms(ctx, ['bot_admin'])
        if tmp:
            await self.bot.say(ctx.message.author.mention + ' You are a bot admin! :smiley:')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin! :slight_frown:')

    @commands.command(pass_context=True)
    async def addadmin(self, ctx, target: discord.Member):
        """Add a user to the bot admin list.
        Syntax: addadmin [user]"""
        tmp = await check_perms(ctx, ['bot_admin'])
        if tmp:
            aentry = str(target)
            rstore = await store.dump()
            if aentry not in rstore['bot_admins']:
                rstore['bot_admins'].extend([aentry])
                await store.write(rstore)
                await self.bot.say('The user specified has successfully been added to the bot admin list!')
            else:
                await self.bot.say('The user specified is already a bot admin!')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin, so you may not add others as admins!')

    @commands.command(pass_context=True)
    async def rmadmin(self, ctx, target: discord.Member):
        """Remove a user from the bot admin list.
        Syntax: rmadmin [user]"""
        tmp = await check_perms(ctx, ['bot_admin'])
        if tmp:
            aentry = str(target)
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

    @commands.command()
    async def adminlist(self):
        """List all bot admins defined.
        Syntax: adminlist"""
        rstore = await store.dump()
        alist = ''
        for i in rstore['bot_admins']:
            alist += i + '\n'
        await self.bot.say('The following people are bot admins:\n' + alist)

    @commands.command(pass_context=True)
    async def getprop(self, ctx, pname: str):
        """Fetch a property from the datastore.
        Syntax: getprop [property name]"""
        pout = await store.get_prop(ctx.message, pname)
        await self.bot.say(pout)

    @commands.command(pass_context=True)
    async def setprop(self, ctx, pname: str, value: str):
        """Set the value of a property on server level.
        Syntax: setprop [property name] [value]"""
        await echeck_perms(ctx, ['server_admin'])
        await store.set_prop(ctx.message, 'by_server', pname, value)
        await self.bot.say('Successfully set `{0}` as `{1}`!'.format(pname, value))

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

#    @commands.command(pass_context=True, )
