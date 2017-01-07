"""Welcome and goodbye messages."""
import discord
import util.commands as commands
from util.const import bool_true
from .cog import Cog

welcome = '''Welcome {0.mention} to **{1.name}**. Have a good time here! :wink:
{2}Learn more about me with `{3}help`.'''
goodbye = ''':eyes: **{0}** has just left this server. Bye!
**{1.name}** just lost a {2}. We'll miss you!'''
class Welcome(Cog):
    """Welcomes and goodbyes. 🤗"""

    async def on_member_join(self, member: discord.Member):
        """On_member_join event for newly joined members."""
        if self.bot.selfbot: return
        target = member.server
        cemotes = member.server.emojis
        em_string = ''
        if cemotes:
            em_string = 'Try some custom emotes: ' + ' '.join([str(i) for i in cemotes]) + '! '
            if len(em_string) >= (1980 - len(welcome)):
                em_string = ''
        bc = await self.store.get_prop(member, 'broadcast_join')
        cmdfix = await self.store.get_prop(member, 'command_prefix')
        if str(bc).lower() in bool_true:
            try:
                await self.bot.send_message(target, welcome.format(member, target, em_string, cmdfix))
            except discord.Forbidden:
                self.logger.warning(f'Couldn\'t announce join of {member} to {member.server}')

    async def on_member_remove(self, member: discord.Member):
        """On_member_remove event for members leaving."""
        if self.bot.selfbot: return
        target = member.server
        bc = await self.store.get_prop(member, 'broadcast_leave')
        if str(bc).lower() in bool_true:
            utype = ('bot' if member.bot else 'member')
            try:
                await self.bot.send_message(target, goodbye.format(str(member), target, utype))
            except discord.Forbidden:
                self.logger.warning(f'Couldn\'t announce leave of {member} from {member.server}')

def setup(bot):
    bot.add_cog(Welcome(bot))
