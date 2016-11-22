"""Definition of the bot's Cosmetic module.'"""
from discord.ext import commands
import util.datastore as store
import util.ranks as rank
from .cog import Cog

class Cosmetic(Cog):
    """Commands for some colorful fun!
    Includes color changing and more.
    """

    @commands.command(aliases=['color'])
    async def role(self, role: str):
        """Set a public role on your account.
        Syntax: role [role name]"""
        await self.bot.say('Role setting is not implemented yet!')

    @commands.command(pass_context=True, aliases=['rank', 'level', 'lvl', 'exp', 'levels'])
    async def xp(self, ctx):
        stat_fmt = '''{0.author.mention} Here are your **stats**:
**LEVEL: {1}
EXPERIENCE: __{2}/{3}__ for next level
TOTAL EXPERIENCE: {4}**
*Try getting some more! :smiley:*
'''
#        if ctx.message.split(' '):
        prof = await store.get_prop(ctx.message, 'profile_' + ctx.message.server.id)
        rlevel = rank.xp_level(prof['exp'])
        await self.bot.say(stat_fmt.format(ctx.message, str(rlevel[0]), str(int(rlevel[1])),
                                           str(int((rlevel[0] + 1) * 75)), str(prof['exp'])))
