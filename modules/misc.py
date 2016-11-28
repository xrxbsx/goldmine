"""Definition of the bot's Miscellaneous module.'"""
import asyncio
from discord.ext import commands
from .cog import Cog

class Misc(Cog):
    """Random commands that can be useful here and there.
    This can be... truly random. Don't be scared! :smile:
    """

    @commands.command(aliases=['g'])
    async def lmgtfy(self, *args):
        """Generates a Let Me Google That For You link.
        Syntax: lmgtfy [search terms]"""
        await self.bot.say('http://lmgtfy.com/?q=' + '+'.join(args))
