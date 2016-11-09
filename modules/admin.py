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

    @commands.command()
    async def update(self):
        """Auto-updates this bot and restarts if any code was updated."""
        await self.bot.say('Running `git pull`...\nOutput: ')
        gitout = subprocess.check_output(['git', 'pull', '-v', '--ff'], stderr=subprocess.STDOUT)
        await self.bot.say('```' + gitout + '```')
        if gitout == 'Already up-to-date.\n':
            await self.bot.say('Bot is already up-to-date, not restarting.')
        else:
            await self.bot.say('Bot was able to update, now restarting.')
            await self.restart()

    @commands.command()
    async def restart(self):
        """Restarts this bot."""
        await self.bot.say('Goldmine is now restarting!')
        exit(0)
