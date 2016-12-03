"""Definition of the bot's Utility module.'"""
import asyncio
import time
import random
import discord
from discord.ext import commands
from google import search
from util.safe_math import eval_expr as emath
from util.const import _mention_pattern, _mentions_transforms
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
        t_game = target.game
        try:
            t_roles.remove(target.server.default_role)
        except ValueError:
            pass
        r_embed = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
        r_embed.set_author(name=str(target), url='http://khronodragon.com', icon_url=avatar_link)
        r_embed.set_thumbnail(url=avatar_link) #top right
        r_embed.set_footer(text=str(target), icon_url=avatar_link)
        r_embed.add_field(name='Nickname', value=('No nickname set!' if d_name == target.name else d_name), inline=True)
        r_embed.add_field(name='User ID', value=target.id, inline=True)
        r_embed.add_field(name='Creation Time', value=target.created_at.strftime(absfmt), inline=True)
        r_embed.add_field(name='Server Join Time', value=target.joined_at.strftime(absfmt), inline=True)
        r_embed.add_field(name='Roles', value=', '.join([str(i) for i in t_roles]) if t_roles else 'User has no roles!', inline=True)
        r_embed.add_field(name='Status', value=status_map[str(target.status)])
        r_embed.add_field(name='Currently Playing', value=(str(t_game) if t_game else 'Nothing!'))
        await self.bot.send_message(ctx.message.channel, embed=r_embed)

    @commands.command(pass_context=True, aliases=['gm'])
    async def info(self, ctx):
        """Get bot info."""
        ch_fmt = '''Total: {0}
Text: {1}
Voice: {2}
DM: {3}
Group DM: {4}'''
        absfmt = '%a %b %d, %Y %I:%M %p UTC'
        status_map = {
            'online': 'Online',
            'offline': 'Offline',
            'idle': 'Idle',
            'dnd': 'Do Not Disturb'
        }
        target = self.bot.user
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        ach = list(self.bot.get_all_channels())
        chlist = [len(ach), 0, 0, 0, 0]
        for i in ach:
            at = str(i.type)
            if at == 'text':
                chlist[1] += 1
            elif at == 'voice':
                chlist[2] += 1
            elif at == 'private':
                chlist[3] += 1
            elif at == 'group':
                chlist[4] += 1
        emb = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
        emb.set_author(name=str(target), url='http://khronodragon.com', icon_url=avatar_link)
        emb.set_thumbnail(url=avatar_link) #top right
        emb.set_footer(text='Made in Python 3.3+', icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/400px-Python-logo-notext.svg.png')
        emb.add_field(name='Servers Accessible', value=len(self.bot.servers), inline=True)
        emb.add_field(name='Author', value='Dragon5232#1841', inline=True)
        emb.add_field(name='Library', value='discord.py', inline=True)
        emb.add_field(name='Members Seen', value=len(list(self.bot.get_all_members())), inline=True)
        emb.add_field(name='Channels Accessible', value=ch_fmt.format(*[str(i) for i in chlist]), inline=True)
        emb.add_field(name='Local Time', value=time.strftime(absfmt, time.localtime()), inline=True)
        emb.add_field(name='ID', value=target.id, inline=True)
        await self.bot.send_message(ctx.message.channel, embed=emb)

    @commands.command(pass_context=True, aliases=['embedhelp', 'embedshelp', 'emhelp', 'ebhelp', 'embhelp'])
    async def ehelp(self, ctx, *commands: str):
        """Shows this message."""
        bot = ctx.bot
        destination = ctx.message.author if bot.pm_help else ctx.message.channel

        await bot.send_message(destination, embed=bot.formatter.eformat_help_for(ctx, bot))

    @commands.command(aliases=['g', 'search', 's', 'query', 'q'])
    async def google(self, *rawin: str):
        intxt = ' '.join(rawin)
        f_query = await self.bot.google(intxt, stop=5)
        await self.bot.say('Google returned: ' + list(f_query)[0])
