"""Definition of the bot's Cosmetic module.'"""
from discord.ext import commands
import util.datastore as store
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

    @commands.command(pass_context=True, aliases=['rank', 'level', 'lvl'])
    async def xp(self, ctx):
        stat_fmt = '''{0.author.mention} Here are your **stats**:
**LEVEL: 1
EXPERIENCE: __{1}/{2}__
TOTAL EXP: {3}**
*Try getting some more! :smiley:*
'''
        rs = await store.dump()
        prof = await store.get_prop(ctx.message, 'profile')
        await self.bot.say(stat_fmt.format(ctx.message, str(prof['exp']), str(rs['levels'][str(prof['level'])]['exp_required']), str(prof['total_exp'])))
