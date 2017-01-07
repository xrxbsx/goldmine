"""Miscellaneous stuff."""
import util.commands as commands
from .cog import Cog

class Misc(Cog):
    """Random commands that can be useful here and there.
    This can be... truly random. Don't be scared! 😄
    """

    @commands.command()
    async def lmgtfy(self, *terms: str):
        """Generate a Let Me Google That For You link.
        Usage: lmgtfy [search terms]"""
        await self.bot.say('http://lmgtfy.com/?q=' + '+'.join(terms))

    @commands.command()
    async def buzz(self, *count: int):
        """Barry Bee Benson Buzz :smirk:
        Usage: buzz"""
        fn_i = 8
        if count:
            fn_i = count[0]
        await self.bot.say('\n'.join(reversed(['buzz ' * i for i in range(fn_i)])))

    @commands.command()
    async def test(self):
        """Do a basic test of the bot.
        Usage: test"""
        await self.bot.reply('everything is looking good! :smiley:')

def setup(bot):
    c = Misc(bot)
    bot.add_cog(c)
