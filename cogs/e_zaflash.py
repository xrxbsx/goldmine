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
    del bot.commands['update']
    del bot.commands['purge']
    for a in (bot.commands['eref'].aliases + bot.commands['seref'].aliases):
        del bot.commands[a]
    del bot.commands['eref']
    del bot.commands['seref']
    bot.game['type'] = 0
    bot.game['name'] = 'with the Owner'
    bot.game['url'] = ''
    del bot.commands['info']
    del bot.commands['gm']
    del bot.commands['home']
    bot.description = 'ZaFlash\'s cool and shiny bot.'
