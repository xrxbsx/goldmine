import asyncio
import io
import random

import discord
from discord.ext import commands


class Cosmetic:
    """Commands for some colorful fun!
    Includes color changing and more.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def role(self, role: str):
        """Set a public role on your account."""
        await self.bot.say('Role setting is not implemented yet!')

    @commands.command()
    async def color(self, role: str):
        """Set the color of your name. Alias to role."""
        await self.role(role) #not working
