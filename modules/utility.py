"""Definition of the bot's Utility module.'"""
import asyncio
import time
from fnmatch import filter
import random
from datetime import datetime
import discord
from discord.ext import commands
from google import search
from util.safe_math import eval_expr as emath
from util.const import _mention_pattern, _mentions_transforms
from util.perms import check_perms
from util.fake import FakeContextMember, FakeMessageMember
from properties import bot_owner
from .cog import Cog

class Utility(Cog):
    """Random commands that can be useful here and there.
    Settings, properties, and other stuff can be found here.
    """

    def __init__(self, bot):
        self.running_ping = []
        super().__init__(bot)

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
        await self.bot.say('\u200b' + ' '.join(args))

    @commands.command(aliases=['calculate', 'calculator', 'math', 'emath', 'eval', 'evaluate'])
    async def calc(self, *args):
        """Evaluates a mathematical experssion.
        Syntax: calc [expression]"""
        await self.bot.say('```python\n' + str(emath(' '.join(args))) + '```')

    @commands.command(pass_context=True, aliases=['about', 'whois', 'who'])
    async def user(self, ctx, *users: str):
        """Extract information about an user.
        Syntax: user"""
        absfmt = '%a %b %d, %Y %I:%M %p UTC'
        status_map = {
            'online': 'Online',
            'offline': 'Offline',
            'idle': 'Idle',
            'dnd': 'Do Not Disturb'
        }
        targets = []
        s = ctx.message.server
        if users:
            members = {}
            for i in s.members:
                members[i.mention] = i
                members[i.id] = i
                members[i.display_name] = i
                members[i.name] = i
            for i in users:
                member = s.get_member(i)
                if member:
                    targets.append(member)
            names = []
            _i = 0
            while _i < len(users):
                names.append(users[_i])
                try:
                    if ' '.join(names) in members:
                        targets.append(members[' '.join(names)])
                        names = []
                    elif _i + 1 == len(users):
                        targets.append(members[users[0]])
                        _i = -1
                        users = users[1:]
                        names = []
                except KeyError as e:
                    await self.bot.say('User **%s** not found, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!' % str(e).strip("'"))
                _i += 1
            if not targets:
                await self.bot.say('**No matching users, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!**')
                return
        else:
            targets.append(ctx.message.author)
        for target in targets:
            au = target.avatar_url
            avatar_link = (au if au else target.default_avatar_url)
            d_name = target.display_name
            t_roles = target.roles
            t_game = target.game
            b_roles = []
            tg_ctx = FakeContextMember(FakeMessageMember(target))
            c_srv = await check_perms(tg_ctx, ['server_admin'])
            c_own = bool(target.id == bot_owner)
            c_adm = await check_perms(tg_ctx, ['bot_admin'])
            c_sown = await check_perms(tg_ctx, ['server_owner'])
            if c_own:
                b_roles.append('Bot Owner')
            if c_adm:
                b_roles.append('Bot Admin')
            if c_srv:
                b_roles.append('Server Admin')
            try:
                t_roles.remove(target.server.default_role)
            except ValueError:
                pass
            r_embed = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
            r_embed.set_author(name=str(target), url='http://khronodragon.com', icon_url=avatar_link)
            r_embed.set_thumbnail(url=avatar_link) #top right
            r_embed.set_footer(text=str(target), icon_url=avatar_link)
            r_embed.add_field(name='Nickname', value=('No nickname set :frowning:' if d_name == target.name else d_name))
            r_embed.add_field(name='User ID', value=target.id)
            r_embed.add_field(name='Creation Time', value=target.created_at.strftime(absfmt))
            r_embed.add_field(name='Server Join Time', value=target.joined_at.strftime(absfmt))
            r_embed.add_field(name='Server Roles', value=', '.join([str(i) for i in t_roles]) if t_roles else 'User has no server roles :frowning:')
            r_embed.add_field(name='Bot Roles', value=', '.join(b_roles) if b_roles else 'User has no bot roles :frowning:')
            r_embed.add_field(name='Status', value=status_map[str(target.status)])
            r_embed.add_field(name='Currently Playing', value=(str(t_game) if t_game else 'Nothing :frowning:'))
            await self.bot.send_message(ctx.message.channel, embed=r_embed)

    @commands.command(pass_context=True, aliases=['gm'])
    async def info(self, ctx):
        """Get bot info.
        Syntax: info"""
        ch_fmt = '''Total: {0}
Text: {1}
Voice: {2}
DM: {3}
Group DM: {4}'''
        absfmt = '%a %b %d, %Y %I:%M:%S %p'
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
        time_diff = datetime.now() - self.bot.start_time
        emb = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
        emb.set_author(name=str(target), url='http://khronodragon.com', icon_url=avatar_link)
        emb.set_thumbnail(url=avatar_link) #top right
        emb.set_footer(text='Made in Python 3.3+', icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/400px-Python-logo-notext.svg.png')
        emb.add_field(name='Servers Accessible', value=len(self.bot.servers))
        emb.add_field(name='Author', value='Dragon5232#1841')
        emb.add_field(name='Version', value=self.bot.version)
        emb.add_field(name='Uptime', value='{0} mins {1} secs'.format(*[round(i, 2) for i in divmod(time_diff.total_seconds(), 60)]))
        emb.add_field(name='Library', value='discord.py')
        emb.add_field(name='Git Revision', value=self.bot.git_rev)
        emb.add_field(name='Commands', value=str(len(self.bot.commands)))
        emb.add_field(name='Lines of Code', value=self.bot.lines)
        emb.add_field(name='Characters of Code', value=self.bot.chars)
        emb.add_field(name='Words in Code', value=self.bot.words)
        emb.add_field(name='Cogs Loaded', value=len(self.bot.cogs))
        emd.add_field(name='Memory Used', value='')
        emb.add_field(name='Modules Loaded', value=len(self.bot.modules))
        emb.add_field(name='Members Seen', value=len(list(self.bot.get_all_members())))
        emb.add_field(name='Channels Accessible', value=ch_fmt.format(*[str(i) for i in chlist]))
        emb.add_field(name='Local Time', value=time.strftime(absfmt, time.localtime()))
        emb.add_field(name='ID', value=target.id)
        await self.bot.send_message(ctx.message.channel, embed=emb)

    @commands.command(pass_context=True, aliases=['embedhelp', 'embedshelp', 'emhelp', 'ebhelp', 'embhelp'])
    async def ehelp(self, ctx, *commands: str):
        """Shows an experimental embed-based help.
        Syntax: ehelp|embedhelp"""
        bot = ctx.bot
        destination = ctx.message.author if bot.pm_help else ctx.message.channel
        pages = bot.formatter.format_help_for(ctx, bot)
        for page in pages:
            await bot.send_message(destination, embed=discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16), description=page.replace('```diff', '').replace('```', ''), title='Bot Help in Embed!'))

    @commands.command(aliases=['g', 'search', 's', 'query', 'q'])
    async def google(self, *rawin: str):
        """Search something on Google.
        Syntax: google [search terms]"""
        intxt = ' '.join(rawin)
        f_query = await self.bot.google(intxt, stop=5)
        fql = list(f_query)
        await self.bot.say('Google returned: ' + fql[0] + ' and ' + fql[1])

    @commands.command(pass_context=True, aliases=['ping', 'pong', 'delay', 'net', 'network', 'lag', 'netlag'])
    async def latency(self, ctx):
        """Get the current network latency to Discord.
        Syntax: latency"""
        begin_time = datetime.now()
        if ctx.message.server.id in self.running_ping:
            await self.bot.say('**A latency test is already being run in this server, wait for it to finish!**')
        else:
            self.running_ping.append(ctx.message.server.id)
            msg = await self.bot.say('Getting latency... `0`')
            for i in range(4):
                await self.bot.edit_message(msg, 'Getting latency... `%s`' % str(i + 1))
            time_diff = datetime.now() - begin_time
            await self.bot.edit_message(msg, 'Latency is: %sms.' % str(round((time_diff.total_seconds() / 5) * 1000, 2)))
            await asyncio.sleep(1.75)
            self.running_ping.remove(ctx.message.server.id)

    @commands.command(pass_context=True)
    async def test(self, ctx):
        """Do a basic test of the bot.
        Syntax: test"""
        await self.bot.say('Everything is looking good, ' + ctx.message.author.mention + '! :smiley:')
