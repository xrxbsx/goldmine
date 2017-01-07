"""Server stats reporting."""
import util.commands as commands
from .cog import Cog

class DiscordBots(Cog):
    """Reporter of server stats to services like Discord Bots."""

def setup(bot):
    bot.add_cog(DiscordBots(bot))
