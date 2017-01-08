"""Small moderation cog."""
import re
import util.commands as commands
from .cog import Cog

class Moderation(Cog):
    """Some moderation at least."""

    async def on_message(self, msg):
        if (len(re.findall(r'_', msg)) >= 1998) or (len(re.findall(r'\*', msg)) >= 1998):
            await self.bot.delete_message(msg)
            await self.bot.send_message(msg.channel, msg.author.mention + ' **:japanese_goblin: No crashing poor iOS users!**')

def setup(bot):
    bot.add_cog(Moderation(bot))
