"""Awesome cog."""
import util.commands as commands
from .cog import Cog

class MyCog(Cog):
    """My awesome cog."""

def setup(bot):
    bot.add_cog(MyCog(bot))
