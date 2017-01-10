"""Nice selfbot goodies."""
import util.commands as commands
from .cog import Cog

class SelfbotGoodies(Cog):
    """Some nice things for selfbot goodies."""

    @commands.command()
    async def screenshot(self):
        await self.bot.upload(fp=)

def setup(bot):
    bot.add_cog(SelfbotGoodies(bot))
