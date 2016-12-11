"""Definition of the bot's Miscellaneous module.'"""
import asyncio
import util.commands as commands
from .cog import Cog

class Miscellaneous(Cog):
    """Random commands that can be useful here and there.
    This can be... truly random. Don't be scared! :smile:
    """

    @commands.command()
    async def lmgtfy(self, *args):
        """Generates a Let Me Google That For You link.
        Syntax: lmgtfy [search terms]"""
        await self.bot.say('http://lmgtfy.com/?q=' + '+'.join(args))

    @commands.command()
    async def buzz(self, *count: int):
        """Barry Bee Benson Buzz :smirk:"""
        fn_i = 8
        if count:
            fn_i = count[0]
        await self.bot.say('\n'.join(reversed(['buzz ' * i for i in range(fn_i)])))

def setup(bot):
    c = Miscellaneous(bot)
    bot.add_cog(c)