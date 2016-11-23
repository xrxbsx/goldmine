"""Definition of the bot's Utility module.'"""
import discord
from discord.ext import commands
from util.safe_math import eval_expr as emath
from .cog import Cog

class Utility(Cog):
    """Random commands that can be useful here and there.
    Settings, properties, and other stuff can be found here.
    """

    @commands.command(pass_context=True)
    async def icon(self, ctx):
        """Retrive the current server's icon.
        Syntax: icon"""
        sname = '**' + ctx.message.server.name + '**'
        iurl = ctx.message.server.icon_url
        if iurl != '':
            await self.bot.say('Here is the link to the icon for ' + sname + ': <' + iurl + '>')
        else:
            await self.bot.say('The current server, ' + sname + ', does not have an icon set! :slight_frown:')

    @commands.command()
    async def say(self, *args):
        """Simply sends the input as a message. For testing.
        Syntax: say [message]"""
        await self.bot.say(' '.join(args))

    @commands.command()
    async def calc(self, *args):
        """Evaluates a mathematical experssion.
        Syntax: calc [expression]"""
        await self.bot.say(emath(' '.join(args)))

    @commands.command(pass_context=True, aliases=['about', 'whois', 'who'])
    async def user(self, ctx, target: discord.Member):
        """Extract information about an user.
        Syntax: user"""
        absfmt = '%a %b %d, %Y %I:%M %p UTC'
        status_map = {
            'online': 'Online',
            'offline': 'Offline',
            'idle': 'Idle',
            'dnd': 'Do Not Disturb'
        }
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        d_name = target.display_name
        t_roles = target.roles
        try:
            t_roles.remove(target.server.default_role)
        except ValueError:
            pass
        r_embed = discord.Embed()
        r_embed.set_author(name=str(target), url='http://khronodragon.com', icon_url=avatar_link)
        r_embed.set_thumbnail(url=avatar_link) #top right
        r_embed.set_footer(text=str(target), icon_url=avatar_link)
        r_embed.add_field(name='Nickname', value=('No nickname set!' if d_name == target.name else d_name), inline=True)
        r_embed.add_field(name='User ID', value=target.id, inline=True)
        r_embed.add_field(name='Creation Time', value=target.created_at.strftime(absfmt), inline=True)
        r_embed.add_field(name='Server Join Time', value=target.joined_at.strftime(absfmt), inline=True)
        r_embed.add_field(name='Roles', value=', '.join([str(i) for i in t_roles]), inline=True)
        r_embed.add_field(name='Status', value=status_map[str(target.status)])
        await self.bot.send_message(ctx.message.channel, embed=r_embed)
