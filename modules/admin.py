import asyncio
import io
import subprocess

import discord
from discord.ext import commands


class Admin:
    """Commands useful for admins and/or moderators.
    Can be extremely powerful, use with caution!
    """
    def __init__(self, bot):
        self.bot = bot

    def is_me(self, mem):
        """Checks if author of a message is this bot."""
        return mem.author == bot.user

    @commands.command()
    async def purge(self, channel: discord.Channel):
        """Removes all of this bot's messages on a channel."""
        deleted = await self.bot.purge_from(channel, limit=200, check=self.is_me)
        await self.bot.send_message(channel, 'Deleted {} message(s)'.format(len(deleted)))

    @commands.command()
    async def nuke(self, channel: discord.Channel):
        """NUKES a channel by deleting all messages!"""
        deleted = await self.bot.purge_from(channel, limit=1000)
        await self.bot.send_message(channel, 'Deleted {} message(s)'.format(len(deleted)))

    @commands.command()
    async def say(self, *args):
        """Simply sends the input as a message. For testing."""
        await self.bot.say(' '.join(args))

    @commands.command(pass_context=True)
    async def update(self, ctx):
        """Auto-updates this bot and restarts if any code was updated."""
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

    @commands.command()
    async def restart(self):
        """Restarts this bot."""
        await self.bot.say('Goldmine is now restarting!')
        exit(0)
