"""Game night!"""
import asyncio
import util.commands as commands
from .cog import Cog

class GameNight(Cog):
    """Now's your chance to have a quick and easy game night!"""

    @commands.command(aliases=['ny', 'nyet', 'noty'])
    async def notyet(self):
        """Not yet, coming Soon™!"""
        await self.bot.say('⚠ Not finished yet!')

def setup(bot):
    c = GameNight(bot)
    bot.add_cog(c)
