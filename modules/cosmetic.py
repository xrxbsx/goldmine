"""Definition of the bot's Cosmetic module.'"""
import discord
from discord.ext import commands
from .cog import Cog

class Cosmetic(Cog):
    """Commands for some colorful fun!
    Includes color changing and more.
    """

    @commands.command()
    async def role(self, role: str):
        """Set a public role on your account.
        Syntax: role [role name]"""
        await self.bot.say('Role setting is not implemented yet!')

    @commands.command()
    async def color(self, role: str):
        """Set the color of your name. Alias to role.
        Synrax: color [color name]"""
        await self.role(role) #not working
