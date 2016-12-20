"""Definition of the bot's ZaFlash module."""
import asyncio
import util.commands as commands
from .cog import Cog

class ZaFlash(Cog):
    """The special stuff for ZaFlash and his clan."""

    @commands.command()
    async def tag(self):
        """Say the clan tag.
        Syntax: tag"""
        await self.bot.say('一ƵƑ⚡')

def setup(bot):
    c = ZaFlash(bot)
    bot.add_cog(c)
    del bot.commands['purge']
