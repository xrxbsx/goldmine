"""Definition of the bot's Utility module.'"""
import asyncio
import time
import sys
from fnmatch import filter
import re
import random
from datetime import datetime, timedelta
from collections import OrderedDict
import discord
import util.commands as commands
from util.safe_math import eval_expr as emath
from util.const import _mention_pattern, _mentions_transforms, home_broadcast
from util.perms import check_perms
from util.fake import FakeContextMember, FakeMessageMember
from properties import bot_owner
from .cog import Cog

if sys.platform in ['linux', 'linux2', 'darwin']:
    import resource

class Utility(Cog):
    """Random commands that can be useful here and there.
    Settings, properties, and other stuff can be found here.
    """
    def __init__(self, bot):
        self.stopwatches = []
        super().__init__(bot)

    @commands.command(pass_context=True, no_pm=True)
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
            try:
                for i in s.members:
                    members[i.mention] = i
                    members[i.id] = i
                    members[i.display_name] = i
                    members[i.name] = i
            except AttributeError:
                pass
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
                try:
                    if ' '.join(names) in members:
                        targets.append(members[' '.join(names)])
                        names = []
                    elif _i + 1 == len(users):
                        targets.append(members[users[0]])
                        _i = -1
                        users = users[1:]
                        names = []
                except KeyError:
                    pass
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
            try:
                t_roles = target.roles
            except AttributeError:
                t_roles = []
            try:
                t_game = target.game
            except AttributeError:
                t_game = None
            b_roles = []
            c_srv = False
            c_sown = False
            try:
                tg_ctx = FakeContextMember(FakeMessageMember(target), self.bot)
            except AttributeError:
                tg_ctx = None
            else:
                c_srv = await check_perms(tg_ctx, ['server_admin'])
                c_sown = await check_perms(tg_ctx, ['server_owner'])
            c_own = bool(target.id == bot_owner)
            c_adm = bool(target.id in self.dstore['bot_admins'])
            is_server = bool(isinstance(target, discord.Member))
            if c_own:
                b_roles.append('Bot Owner')
            if c_adm:
                b_roles.append('Bot Admin')
            if c_srv:
                b_roles.append('Server Admin')
            try:
                t_roles.remove(target.server.default_role)
            except (ValueError, AttributeError):
                pass
            r_embed = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
            r_embed.set_author(name=str(target), url='https://blog.khronodragon.com/', icon_url=avatar_link)
            r_embed.set_thumbnail(url=avatar_link) #top right
            r_embed.set_footer(text=str(target), icon_url=avatar_link)
            r_embed.add_field(name='Nickname', value=('No nickname set :frowning:' if d_name == target.name else d_name))
            r_embed.add_field(name='User ID', value=target.id)
            r_embed.add_field(name='Creation Time', value=target.created_at.strftime(absfmt))
            r_embed.add_field(name='Server Join Time', value=target.joined_at.strftime(absfmt) if is_server else 'Couldn\'t fetch')
            r_embed.add_field(name='Server Roles', value=', '.join([str(i) for i in t_roles]) if t_roles else 'User has no server roles :frowning:')
            r_embed.add_field(name='Bot Roles', value=', '.join(b_roles) if b_roles else 'User has no bot roles :frowning:')
            r_embed.add_field(name='Status', value=status_map[str(target.status)] if is_server else 'Couldn\'t fetch')
            r_embed.add_field(name='Currently Playing', value=(str(t_game) if t_game else 'Nothing :frowning:'))
            await self.bot.say(embed=r_embed)

    @commands.command(pass_context=True, aliases=['gm'])
    async def info(self, ctx):
        """Get bot info.
        Syntax: info"""
        ch_fmt = '''Total: {0}
Text: {1}
Voice: {2}
DM: {3}'''
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
        chlist = [len(ach), 0, 0, 0]
        for i in ach:
            at = str(i.type)
            if at == 'text':
                chlist[1] += 1
            elif at == 'voice':
                chlist[2] += 1
            elif at == 'private':
                chlist[3] += 1
        up = await self.bot.format_uptime()
        raw_musage = 0
        got_conversion = False
        musage_dec = 0
        musage_hex = 0
        if sys.platform.startswith('linux'): # Linux & Windows report in kilobytes
            raw_musage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            got_conversion = True
            musage_dec = raw_musage / 1000
            musage_hex = raw_musage / 1024
        elif sys.platform == 'darwin': # Mac reports in bytes
            raw_musage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            got_conversion = True
            musage_dec = raw_musage / 1000000 # 1 million. 1000 * 1000
            musage_hex = raw_musage / 1048576 # 1024 * 1024
        emb = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
        emb.set_author(name=str(target), url='https://blog.khronodragon.com/', icon_url=avatar_link)
        emb.set_thumbnail(url=avatar_link) #top right
        emb.set_footer(text='Made in Python 3.3+ with Discord.py %s' % self.bot.lib_version, icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/400px-Python-logo-notext.svg.png')
        emb.add_field(name='Servers Accessible', value=len(self.bot.servers))
        emb.add_field(name='Author', value='Dragon5232#1841')
        emb.add_field(name='Version', value=self.bot.version)
        emb.add_field(name='Uptime', value=up)
        emb.add_field(name='Library', value='discord.py')
        emb.add_field(name='Library Version', value=self.bot.lib_version)
        emb.add_field(name='Git Revision', value=self.bot.git_rev)
        emb.add_field(name='Commands', value=str(len(self.bot.commands)))
        emb.add_field(name='Files of Code', value=self.bot.files)
        emb.add_field(name='Lines of Code', value=self.bot.lines)
        emb.add_field(name='Characters of Code', value=self.bot.chars)
        emb.add_field(name='Words in Code', value=self.bot.words)
        emb.add_field(name='Code Size', value=str(round(self.bot.size_kb, 1)) + ' KB')
        emb.add_field(name='Average File Size', value=str(round(self.bot.avg_size_kb, 1)) + ' KB')
        emb.add_field(name='Cogs Loaded', value=len(self.bot.cogs))
        emb.add_field(name='Memory Used', value=(str(round(musage_dec, 1)) + ' MB (%s MiB)' % str(round(musage_hex, 1))) if got_conversion else 'Couldn\'t fetch')
        emb.add_field(name='Modules Loaded', value=len(self.bot.modules))
        emb.add_field(name='Members Seen', value=len(list(self.bot.get_all_members())))
        emb.add_field(name='Channels', value=ch_fmt.format(*[str(i) for i in chlist]))
        emb.add_field(name='Custom Emojis', value=len(list(self.bot.get_all_emojis())))
        emb.add_field(name='Local Time', value=time.strftime(absfmt, time.localtime()))
        emb.add_field(name='ID', value=target.id)
        emb.add_field(name='My Homeland', value='https://blog.khronodragon.com')
        emb.add_field(name='Invite Link', value='https://tiny.cc/goldbot')
        await self.bot.say(home_broadcast, embed=emb)

    @commands.command(pass_context=True, aliases=['embedhelp', 'embedshelp', 'emhelp', 'ebhelp', 'embhelp'])
    async def ehelp(self, ctx, *commands: str):
        """Shows an experimental embed-based help.
        Syntax: ehelp|embedhelp"""
        bot = ctx.bot
        destination = ctx.message.author if bot.pm_help else ctx.message.channel
        pages = bot.formatter.format_help_for(ctx, bot)
        target = self.bot.user
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        for page in pages:
            emb = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16), description=page.replace('```diff', '').replace('```', ''), title='Commands & Other Help')
            emb.set_author(name=str(self.bot.user), icon_url=avatar_link, url='https://blog.khronodragon.com/')
            await bot.send_message(destination, embed=emb)

    @commands.command(aliases=['g', 'search', 's', 'query', 'q'])
    async def google(self, *rawin: str):
        """Search something on Google.
        Syntax: google [search terms]"""
        if rawin:
            intxt = ' '.join(rawin)
            fql = await self.bot.google(intxt, num=2)
            try:
                await self.bot.say('Google returned: ' + fql[0] + ' and ' + fql[1])
            except IndexError:
                await self.bot.say('**There were no results!**')
        else:
            await self.bot.say('**You must specify some search terms!**')

    @commands.cooldown(1, 9.5, type=commands.BucketType.server)
    @commands.command(pass_context=True, aliases=['ping', 'pong', 'delay', 'net', 'network', 'lag', 'netlag'])
    async def latency(self, ctx):
        """Get the current network latency to Discord.
        Syntax: latency"""
        begin_time = datetime.now()
        msg = await self.bot.say('Getting latency... `0`')
        for i in range(4):
            await self.bot.edit_message(msg, 'Getting latency... `%s`' % str(i + 1))
        time_diff = datetime.now() - begin_time
        await self.bot.edit_message(msg, 'Latency is: %sms.' % str(round((time_diff.total_seconds() / 5) * 1000, 2)))

    @commands.command(pass_context=True)
    async def test(self, ctx):
        """Do a basic test of the bot.
        Syntax: test"""
        await self.bot.say('Everything is looking good, ' + ctx.message.author.mention + '! :smiley:')

    @commands.command(pass_context=True)
    async def uptime(self, ctx):
        """Report the current uptime of the bot.
        Syntax: uptime"""
        up = await self.bot.format_uptime()
        await self.bot.say(ctx.message.author.mention + ' My current uptime is **' + up + '**.')

    @commands.command(pass_context=True, aliases=['link', 'invlink', 'addbot', 'botadd'])
    async def invite(self, ctx, *rids: str):
        """Generate an invite link for myself or another bot.
        Syntax: invite {optional: bot ids}"""
        ids = list(rids)
        msg = ''
        if not ids:
            ids.append(self.bot.user.id)
        for iid in ids:
            try:
                int(iid)
            except ValueError:
                await self.bot.say('**Invalid ID!**')
            else:
                if iid == self.bot.user.id:
                    msg += 'https://discordapp.com/api/oauth2/authorize?client_id={0}&scope=bot&permissions={1} (<https://tiny.cc/goldbot> for short)\n'.format(iid, self.bot.perm_mask)
                else:
                    msg += 'https://discordapp.com/api/oauth2/authorize?client_id={0}&scope=bot&permissions=66321471\n'.format(iid)
        await self.bot.say(msg)

    @commands.command(aliases=['homeland', 'web', 'website', 'webpage'])
    async def home(self):
        """Get the link to my homeland.
        Syntax: home"""
        await self.bot.say(home_broadcast)

    async def poll_task(self, emojis, msg, poll_table):
        while True:
            fnr = await self.bot.wait_for_reaction(emoji=emojis, message=msg, check=lambda r, a: not a == msg.server.me)
            r = fnr.reaction
            if fnr.user not in poll_table[str(r.emoji)]:
                poll_table[str(r.emoji)].append(fnr.user)

    @commands.cooldown(1, 5, type=commands.BucketType.user)
    @commands.command(pass_context=True)
    async def poll(self, ctx, *rquestion: str):
        """Start a public poll with reactions.
        Syntax: poll [emojis] [question] [time in seconds]"""
        async def cem_help():
            if raw_c_emojis:
                try:
                    for i in ctx.message.server.emojis:
                        cem_map[str(i)] = i
                except AttributeError:
                    return
                for i in raw_c_emojis:
                    try:
                        c_emojis.append(cem_map[i])
                    except KeyError:
                        await self.bot.say('**Custom emoji `%s` doesn\'t exist!**' % i)
                        return
                emojis += c_emojis
        question = ''
        if rquestion:
            question = ' '.join(rquestion)
        else:
            await self.bot.say('**You must specify a question!**')
            return
        stime = 0.0
        cem_map = {}
        highpoints = None
        try:
            stime = float(rquestion[-1:][0])
        except ValueError:
            await self.bot.say('**You must provide a valid poll time!**')
            return
        _question = question.split(' ')
        del _question[-1:]
        question = ' '.join(_question)
        try:
            # UCS-4
            highpoints = re.compile(u'[\U00010000-\U0010ffff]')
        except re.error:
            # UCS-2
            highpoints = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
        u_emojis = re.findall(highpoints, question)
        raw_c_emojis = re.findall(re.compile(r'<:[a-z]+:[0-9]{18}>', flags=re.IGNORECASE), question)
        c_emojis = []
        emojis = u_emojis
        await cem_help()
        emojis = list(OrderedDict.fromkeys(emojis))
        for ri in emojis:
            i = str(ri)
            question = question.replace(' ' + i, '')
            question = question.replace(i + ' ', '')
            question = question.replace(i, '')
        question = question.strip()
        if not emojis:
            await self.bot.say('**You must specify some emojis!**')
            return
        msg_key = ctx.message.author.mention + ' is now polling:\n    \u2022 ' + question + '\n'
        msg = await self.bot.say(msg_key + '**POLL NOT ACTIVE YET, ADDING REACTIONS.**')
        for emoji in emojis:
            await self.bot.add_reaction(msg, emoji)
        await self.bot.edit_message(msg, msg_key + '**POLL IS NOW ACTIVE. Give it a vote!**')
        emojis = list(emojis)
        poll_table = OrderedDict((str(i), []) for i in emojis)
        task = asyncio.ensure_future(self.poll_task(emojis, msg, poll_table))
        await asyncio.sleep(stime)
        task.cancel()
        _vote_table = {i: len(poll_table[i]) for i in poll_table}
        vote_table = OrderedDict(reversed(sorted(_vote_table.items(), key=lambda t: t[1])))
        _totals = '\n'.join([str(i) + ': {0} votes'.format(str(vote_table[i])) for i in vote_table])
        winner = max(vote_table, key=vote_table.get)
        await self.bot.say('**Poll time is over, stopped! Winner is...** ' + str(winner) + '\nResults were:\n' + _totals)
        await self.bot.edit_message(msg, msg_key + '**POLL HAS ALREADY FINISHED.**')

        @commands.command(aliases=["sw"], pass_context=True)
        async def stopwatch(self, ctx):
            """A stopwatch for your convenience."""
            author = ctx.message.author
            if not author.id in self.stopwatches:
                self.stopwatches[author.id] = int(time.perf_counter())
                await self.bot.say(author.mention + " Stopwatch started!")
            else:
                tmp = abs(self.stopwatches[author.id] - int(time.perf_counter()))
                tmp = str(timedelta(seconds=tmp))
                await self.bot.say(author.mention + " Stopwatch stopped! Time: **" + tmp + "**")
                self.stopwatches.pop(author.id, None)

def setup(bot):
    c = Utility(bot)
    bot.add_cog(c)
