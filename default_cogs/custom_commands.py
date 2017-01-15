"""Nice and easy... custom commands!"""
import util.commands as commands
from .cog import Cog

class CustomCommands(Cog):
    """Nice and easy... custom commands!"""

    @commands.command(aliases=['ny', 'nyet', 'noty'])
    async def notyet(self):
        """Not yet, coming Soon™!"""
        await self.bot.say('⚠ Not finished yet!')

def setup(bot):
    bot.add_cog(CustomCommands(bot))
