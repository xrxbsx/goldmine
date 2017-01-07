"""Google!"""
import util.commands as commands
from util.google import search
from .cog import Cog

class Google(Cog):
    """Google. We all need it at some point."""

    async def s_google(self, query, num=3):
        """A method of querying Google safe for async."""
        return await search(query, num=num)

    @commands.command(aliases=['g', 'search', 'query', 'q'])
    async def google(self, *text: str):
        """Search something on Google.
        Usage: google [search terms]"""
        if text:
            query = ' '.join(text)
        else:
            await self.bot.reply('you need to specify some search terms!')
            return
        m = ''
        fql = await self.s_google(query, num=2)
        try:
            m = 'Google returned: ' + fql[0]
        except IndexError:
            m = '**There were no results!**'
        if len(fql) >= 2:
            m += ' and ' + fql[1]
        await self.bot.say(m)

def setup(bot):
    bot.add_cog(Google(bot))
