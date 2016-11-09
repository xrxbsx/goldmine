import asyncio
import io
import random

import discord
from discord.ext import commands


class Admin:
    """Commands useful for admins and/or moderators.
    Can be extremely powerful, use with caution!
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def purge(self, channel: discord.Channel):
        """Removes all of this bot's messages on a channel."""
        deleted = await self.bot.purge_from(channel, limit=200, check=is_me)
        await self.bot.send_message(channel, 'Deleted {} message(s)'.format(len(deleted)))

    @commands.command()
    async def nuke(self, channel: discord.Channel):
        """NUKES a channel by deleting all messages!"""
        deleted = await self.bot.purge_from(channel, limit=1000)
        await self.bot.send_message(channel, 'Deleted {} message(s)'.format(len(deleted)))
