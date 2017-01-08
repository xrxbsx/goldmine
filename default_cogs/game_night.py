"""Game night!"""
import asyncio
import util.commands as commands
from .cog import Cog

class GameNight(Cog):
    """Now's your chance to have a quick and easy game night!"""

    @commands.group(pass_context=True, aliases=['game_night'])
    async def gamenight(self):
        """Game night!
        Syntax: gamenight {stuff}"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
        else:
            await self.bot.say('⚠ Not finished yet!')

def setup(bot):
    c = GameNight(bot)
    bot.add_cog(c)
