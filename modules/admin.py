"""Definition of the bot's Admin module.'"""
from __future__ import print_function
import subprocess

import discord
from discord.ext import commands
from util.perms import check_perms
from .cog import Cog

class Admin(Cog):
    """Commands useful for admins and/or moderators.
    Can be extremely powerful, use with caution!
    """

    def is_me(self, mem):
        """Checks if author of a message is this bot."""
        return mem.author == self.bot.user

    async def perm_err(self, ctx):
        """Returns a permission error in the chat."""
        await self.bot.say(ctx.message.author.mention + ' You don\'t have enough **permissions** to execute that command!')

    @commands.command(pass_context=True)
    async def purge(self, ctx, channel: discord.Channel):
        """Removes all of this bot's messages on a channel.
        Syntax: purge [channel name]"""
        if not check_perms(ctx, ['bot_admin']):
            await self.perm_err(ctx)
            return
        deleted = await self.bot.purge_from(channel, limit=200, check=self.is_me)
        await self.bot.send_message(channel, 'Deleted {} message(s)'.format(len(deleted)))

    @commands.command(pass_context=True)
    async def nuke(self, ctx, channel: discord.Channel):
        """NUKES a channel by deleting all messages!
        Syntax: nuke [channel name]"""
        if not check_perms(ctx, ['bot_admin']):
            await self.perm_err(ctx)
            return
        deleted = await self.bot.purge_from(channel, limit=1000)
        await self.bot.send_message(channel, 'Deleted {} message(s)'.format(len(deleted)))

    @commands.command(pass_context=True)
    async def update(self, ctx):
        """Auto-updates this bot and restarts if any code was updated.
        Syntax: update"""
        if not check_perms(ctx, ['bot_admin']):
            await self.perm_err(ctx)
            return
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
            ctx.invoke(self.restart)

    @commands.command(pass_context=True)
    async def restart(self, ctx):
        """Restarts this bot.
        Syntax: restart"""
        if not check_perms(ctx, ['bot_admin']):
            await self.perm_err(ctx)
            return
#        for i in self.bot.servers:
#            await self.bot.send_message(i.default_channel, 'This bot (' + self.bname + ') is now restarting!')
        await self.bot.say('This bot (' + self.bname + ') is now restarting!')
        print('This bot is now restarting!')
        self.bot.is_restart = True
        self.loop.stop()
