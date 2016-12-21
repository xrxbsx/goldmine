"""Definition of the bot's ZaFlash module."""
import asyncio
import util.commands as commands
from util.func import bdel
from util.const import bool_true
from .cog import Cog

class ZaFlash(Cog):
    """The special stuff for ZaFlash and his clan."""

    @commands.command()
    async def tag(self):
        """Say the clan tag.
        Syntax: tag"""
        await self.bot.say('一ƵƑ⚡')

    @commands.command(pass_context=True, hidden=True, aliases=['rderef'])
    async def deref(self, ctx, *, code: str):
        """Evaluate some code in command scope.
        Syntax: deref [code to execute]"""
        if ctx.message.author.id != '160567046642335746':
            await self.bot.say('No permission!')
            return False
        def print(*ina: str):
            asyncio.ensure_future(self.bot.say(' '.join(ina)))
            return True
        try:
            ev_output = eval(bdel(bdel(code, '```python'), '```py').strip('`'))
        except Exception as e:
            ev_output = 'An exception of type %s has occured!\n' % type(e).__name__ + str(e)
        o = str(ev_output)
        if ctx.invoked_with.startswith('r'):
            await self.bot.say(o)
        else:
            await self.bot.say('```py\n' + o + '```')

def setup(bot):
    del bot.commands['update']
    del bot.commands['purge']
    for a in (bot.commands['eref'].aliases + bot.commands['seref'].aliases):
        del bot.commands[a]
    del bot.commands['eref']
    del bot.commands['seref']
    bot.game['type'] = 0
    bot.game['name'] = 'with the Owner'
    bot.game['url'] = ''
    del bot.commands['info']
    del bot.commands['gm']
    del bot.commands['home']
    bot.commands['nuke'].name = 'clear'
    del bot.commands['etest']
    del bot.commands['buzz']
    c = ZaFlash(bot)
    bot.add_cog(c)
    bot.description = 'ZaFlash\'s cool and shiny bot.'
    @bot.event
    async def on_member_join(self, member):
        """On_member_join event for newly joined members."""
        target = {c.name: c for c in member.server.channels}['welcomes-and-goodbyes']
        cemotes = member.server.emojis
        em_string = ''
        if cemotes:
            em_string = ': ' + ' '.join([str(i) for i in cemotes])
        fmt = '''Welcome {0.mention} to **{1.name}**. Have a good time here! :wink:
Remember to use the custom emotes{2} for extra fun! You can access my help with {3}help.'''
        bc = await bot.store.get_prop(member, 'broadcast_join')
        cmdfix = await bot.store.get_prop(member, 'command_prefix')
        if str(bc).lower() in bool_true:
            await bot.send_message(target, fmt.format(member, member.server, em_string, cmdfix))
    @bot.event
    async def on_member_remove(self, member):
        """On_member_remove event for members leaving."""
        target = {c.name: c for c in member.server.channels}['welcomes-and-goodbyes']
        fmt = '''Aw, **{0}** has just left this server. Bye!
**{1.name}** has now lost a {2}. We'll miss you! :bear:'''
        bc = await bot.store.get_prop(member, 'broadcast_leave')
        if str(bc).lower() in bool_true:
            utype = ('bot' if member.bot else 'member')
            await bot.send_message(target, fmt.format(str(member), member.server, utype))
