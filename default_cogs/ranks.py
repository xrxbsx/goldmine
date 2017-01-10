"""Ranks and levels."""
import math
import random
import util.commands as commands
import util.ranks as rank
from util.const import lvl_base, bool_true
from util.fake import FakeMessageMember
from .cog import Cog

class Ranks(Cog):
    """Ranks and levels."""

    async def on_not_command(self, msg):
        """Do level-up logic."""
        if msg.channel.is_private: return
        prof_name = 'profile_' + msg.server.id
        prof = await self.store.get_prop(msg, prof_name)
        prof['exp'] += math.ceil(((len(msg.content) / 6) * 1.5) + random.randint(0, 14))
        new_level = rank.xp_level(prof['exp'])[0]
        if self.bot.status != 'invisible':
            if self.bot.selfbot: return
            if new_level > prof['level']:
                bclu = await self.store.get_prop(msg, 'broadcast_level_up')
                if isinstance(bclu, str):
                    bclu = bclu.lower()
                if bclu in bool_true:
                    await self.bot.msend(msg, '**Hooray!** {0.mention} has just *advanced* to **level {1}**.'.format(msg.author, str(new_level)))
        prof['level'] = new_level
        await self.store.set_prop(msg, 'by_user', prof_name, prof)

    @commands.command(pass_context=True, aliases=['xp', 'level', 'lvl', 'exp', 'levels'], no_pm=True)
    async def rank(self, ctx, *users: str):
        """Check your experience, level, and rank!
        Usage: xp"""
        targets = []
        s = ctx.message.server
        if users:
            members = {}
            for i in getattr(s, 'members', []):
                members[i.mention] = i
                members[i.id] = i
                members[i.display_name] = i
                members[i.name] = i
            for i in users:
                try:
                    member = s.get_member(i)
                except AttributeError:
                    try:
                        member = await self.bot.get_user_info(i)
                    except discord.HTTPException:
                        member = None
                if member:
                    targets.append(member)
                else:
                    try:
                        member = await self.bot.get_user_info(i)
                    except discord.HTTPException:
                        member = None
                    if member:
                        targets.append(member)
            names = []
            _i = 0
            while _i < len(users):
                names.append(users[_i])
                with suppress(KeyError):
                    if ' '.join(names) in members:
                        targets.append(members[' '.join(names)])
                        names = []
                    elif _i + 1 == len(users):
                        targets.append(members[users[0]])
                        _i = -1
                        users = users[1:]
                        names = []
                _i += 1
            if not targets:
                await self.bot.say('**No matching users, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!**')
                return
        else:
            targets.append(ctx.message.author)
        stat_fmt = '''{0.author.mention} Here are {5} **stats**:
**LEVEL: {1}
EXPERIENCE: __{2}/{3}__ for next level
TOTAL EXPERIENCE: {4}**
*Try getting some more! :smiley:*
'''
        for r_tgt in targets:
            target = FakeMessageMember(r_tgt)
            prof = await self.store.get_prop(target, 'profile_' + target.server.id)
            rlevel = rank.xp_level(prof['exp'])
            await self.bot.say(stat_fmt.format(target, str(rlevel[0]), str(int(rlevel[1])),
                                               str(int((rlevel[0] + 1) * lvl_base)), str(prof['exp']), ('your' if target.author.id == ctx.message.author.id else str(target.author) + "'s")))

def setup(bot):
    bot.add_cog(Ranks(bot))
