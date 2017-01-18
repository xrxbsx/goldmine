"""Definition of the bot's Utility module.'"""
from contextlib import suppress
from collections import OrderedDict
from datetime import datetime, timedelta
from fnmatch import filter
from io import BytesIO
from properties import bot_owner
from util.const import _mention_pattern, _mentions_transforms, home_broadcast, absfmt, status_map, ch_fmt, code_stats, eval_blocked, v_level_map
from util.fake import FakeContextMember, FakeMessageMember
from util.func import bdel, async_encode as b_encode, async_decode as b_decode, smartjoin
from util.asizeof import asizeof
from util.perms import check_perms, or_check_perms
import util.dynaimport as di
from .cog import Cog

for mod in ['asyncio', 'random', 're', 'sys', 'time', 'textwrap', 'unicodedata',
            'aiohttp', 'async_timeout', 'discord', 'asteval', 'os']:
    globals()[mod] = di.load(mod)
json = di.load('util.json')
commands = di.load('util.commands')
mclib = di.load('util.mclib')

have_pil = True
print(' - Loading PIL...')
try:
    from PIL import Image, ImageOps
except ImportError:
    print(' - Could not load PIL!')
    have_pil = False

class Utility(Cog):
    """Random commands that can be useful here and there.
    Settings, properties, and other stuff can be found here.
    """
    def __init__(self, bot):
        self.stopwatches = {}
        super().__init__(bot)

    @commands.command(pass_context=True, no_pm=True)
    async def icon(self, ctx):
        """Retrive the current server's icon.
        Usage: icon"""
        sname = '**' + ctx.message.server.name + '**'
        iurl = ctx.message.server.icon_url
        if iurl:
            await self.bot.say('Here is the link to the icon for ' + sname + ': <' + iurl + '>')
        else:
            await self.bot.say('The current server, ' + sname + ', does not have an icon set! :slight_frown:')

    @commands.command(pass_context=True)
    async def say(self, ctx, *, stuffs: str):
        """Simply sends the input as a message. For testing.
        Usage: say [message]"""
        await or_check_perms(ctx, ['bot_admin'])
        try:
            await self.bot.delete_message(ctx.message)
        except discord.Forbidden:
            pass
        await self.bot.say(stuffs)

    async def math_task(self, code: str):
        eval_exc = self.loop.run_in_executor(None, self.bot.asteval.eval, code)
        return await eval_exc

    @commands.command(pass_context=True, name='eval', aliases=['calculate', 'calculator', 'math', 'emath', 'calc', 'evaluate', 'expr', 'expression', 'rcalculate', 'rcalculator', 'rmath', 'remath', 'reval', 'revaluate', 'rexpr', 'rexpression'])
    async def cmd_eval(self, ctx, *, code: str):
        """Evaluate some code, or a math expression.
        Usage: eval [code/expression]"""
        await or_check_perms(ctx, ['bot_admin'])
        code = bdel(bdel(code, '```python').strip('`'), '```py')
        for key in eval_blocked:
            if re.search(key, code):
                await self.bot.say(ctx.message.author.mention + ' **Blocked keyword found!**')
                return False
        try:
            with async_timeout.timeout(3):
                m_result = await self.math_task(code)
        except (asyncio.TimeoutError, RuntimeError) as exp:
            resp = '{0.author.mention} **It took too long to evaluate your expression!**'.format(ctx.message)
            if isinstance(exp, RuntimeError):
                if str(exp).startswith('Execution exceeded time limit, max runtime is '):
                    await self.bot.say(resp)
                    return
                else:
                    raise ValueError('ASTEval Error of type TimeoutError')
            else:
                await self.bot.say(resp)
            return
        _result = ''
        if self.bot.asteval.error:
            err_type = self.bot.asteval.error[0].get_error()[0]
            if err_type == 'MemoryError':
                await self.bot.reset_asteval(reason='due to MemoryError')
                await self.bot.say(ctx.message.author.mention + ' **Please re-run your `eval` command!**')
                return
            elif err_type in ['NameError', 'UnboundLocalError']:
                await self.bot.say(ctx.message.author.mention + ' **You tried to use a variable that didn\'t exist!**')
                return
            else:
                raise ValueError('ASTEval Error of type ' + err_type)
        else:
            try:
                _result = str(m_result)
            except MemoryError:
                await self.bot.reset_asteval(reason='due to MemoryError')
                await self.bot.say(ctx.message.author.mention + ' **Please re-run your `eval` command!**')
                return
        try:
            if m_result is None:
                _result = '✅'
            else:
                if not ctx.invoked_with.startswith('r'):
                    _result = '```py\n' + _result + '```'
        except MemoryError:
            await self.bot.reset_asteval(reason='due to MemoryError')
            await self.bot.say(ctx.message.author.mention + ' **Please re-run your `eval` command!**')
            return
        try:
            byte_size = await self.loop.run_in_executor(None, asizeof, self.bot.asteval.symtable)
            if byte_size > 50_000_000: # 110 MiB 115_343_360, 107 MiB 112_197_632, 107 MB 107_000_000
                await self.bot.reset_asteval(reason='due to memory usage > 50M', note=f'was using {byte_size / 1048576} MiB')
        except MemoryError:
            await self.bot.reset_asteval(reason='due to MemoryError during asizeof')
        else:
            del byte_size
        await self.bot.say(_result)

    @commands.command(pass_context=True, aliases=['whois', 'who'])
    async def user(self, ctx, *users: str):
        """Get tons of info on an user or some users. Spaces, multiuser, and cross-server IDs work.
        Usage: user {user(s)}"""
        targets = []
        s = ctx.message.server
        if users: # huge complicated mess for spaces,
                  # multiuser, nicknames, mentions, IDs,
                  # names, and more in one go.
            members = {}
            for i in getattr(s, 'members', []):
                members[i.mention] = i
                members[i.id] = i
                members[i.display_name] = i
                members[i.name] = i
                members[str(i)] = i
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
        targets = list(OrderedDict.fromkeys(targets))
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
                c_srv = await check_perms(tg_ctx, ['manage_server'])
                c_sown = await check_perms(tg_ctx, ['server_owner'])
            c_own = target.id == bot_owner
            c_adm = target.id in self.dstore['bot_admins']
            is_server = isinstance(target, discord.Member)
            if c_own:
                b_roles.append('Bot Owner')
            if c_adm:
                b_roles.append('Bot Admin')
            if c_srv:
                b_roles.append('Server Admin')
            with suppress(ValueError, AttributeError):
                t_roles.remove(target.server.default_role)
            r_embed = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
            r_embed.set_author(name=str(target), url=avatar_link, icon_url=avatar_link)
            r_embed.set_thumbnail(url=avatar_link) #top right
            r_embed.set_footer(text=str(target), icon_url=avatar_link)
            r_embed.add_field(name='Nickname', value=('No nickname set 😦' if d_name == target.name else d_name))
            r_embed.add_field(name='User ID', value=target.id)
            r_embed.add_field(name='Creation Time', value=target.created_at.strftime(absfmt))
            r_embed.add_field(name='Server Join Time', value=target.joined_at.strftime(absfmt) if is_server else 'Couldn\'t fetch')
            r_embed.add_field(name='Server Roles', value=', '.join([str(i) for i in t_roles]) if t_roles else 'User has no server roles 😦')
            r_embed.add_field(name='Bot Roles', value=', '.join(b_roles) if b_roles else 'User has no bot roles 😦')
            r_embed.add_field(name='Status', value=status_map[str(target.status)] if is_server else 'Couldn\'t fetch')
            r_embed.add_field(name='Currently Playing', value=(str(t_game) if t_game else 'Nothing 😦'))
            await self.bot.say(embed=r_embed)

    @commands.command(pass_context=True, aliases=['server', 's', 'sinfo', 'infos', 'guildinfo', 'guild', 'ginfo', 'infog'], no_pm=True)
    async def serverinfo(self, ctx):
        """Get loads of info about this server.
        Usage: serverinfo"""
        target = self.bot.user
        s = ctx.message.server
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        ach = s.channels
        chlist = [len(ach), 0, 0, '👀']
        for i in ach:
            at = str(i.type)
            if at == 'text':
                chlist[1] += 1
            elif at == 'voice':
                chlist[2] += 1
        iurl = s.icon_url
        s_reg = str(s.region)
        r_embed = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
        r_embed.set_author(name=s.name, url='https://blog.khronodragon.com/', icon_url=(iurl if iurl else avatar_link))
        r_embed.set_footer(text=str(target), icon_url=avatar_link)
        r_embed.add_field(name='ID', value=s.id)
        r_embed.add_field(name='Members', value=len(s.members))
        r_embed.add_field(name='Channels', value=ch_fmt.format(*[str(i) for i in chlist]))
        r_embed.add_field(name='Roles', value=len(s.roles))
        r_embed.add_field(name='Custom Emojis', value=len(s.emojis))
        r_embed.add_field(name='Region (Location)', value=str(s.region).replace('-', ' ').title().replace('Eu ', 'EU ').replace('Us ', 'US ').replace('Vip', 'VIP '))
        r_embed.add_field(name='Owner', value=str(s.owner))
        r_embed.add_field(name='Default Channel', value=f'<#{s.default_channel.id}>\n(#{s.default_channel.name})')
        r_embed.add_field(name='Icon URL', value=(iurl if iurl else 'None 😦'))
        r_embed.add_field(name='Admins Need 2FA', value=('Yes' if s.mfa_level else 'No'))
        r_embed.add_field(name='Verification Level', value=v_level_map[str(s.verification_level)])
        await self.bot.say(embed=r_embed)

    @commands.command(pass_context=True, aliases=['gm', 'goldmine', 'aboutme', 'me', 'about'])
    async def info(self, ctx):
        """Get bot info.
        Usage: info"""
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
        ram = await self.bot.get_ram()
        got_conversion = ram[0]
        emb = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
        emb.set_author(name=str(target), url='https://blog.khronodragon.com/', icon_url=avatar_link)
        emb.set_footer(text='Made in Python 3.6+ with Discord.py %s' % self.bot.lib_version, icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/400px-Python-logo-notext.svg.png')
        emb.add_field(name='Servers Accessible', value=len(self.bot.servers))
        emb.add_field(name='Author', value='Dragon5232#1841')
        emb.add_field(name='Version', value=self.bot.version)
        emb.add_field(name='Uptime', value=up)
        emb.add_field(name='Local Time', value=time.strftime(absfmt, time.localtime()))
        emb.add_field(name='Git Revision', value=self.bot.git_rev)
        emb.add_field(name='Code Stats', value=code_stats.format(files=self.bot.lines, chars=self.bot.chars, lines=self.bot.lines, words=self.bot.words))
        emb.add_field(name='Code Size', value=str(round(self.bot.size_kb, 1)) + ' KB\nAverage: ' + str(round(self.bot.avg_size_kb, 1)) + ' KB')
        emb.add_field(name='Cogs Loaded', value=len(self.bot.cogs))
        emb.add_field(name='Memory Used', value=(str(round(ram[1], 1)) + ' MB (%s MiB)' % str(round(ram[2], 1))) if got_conversion else 'Couldn\'t fetch')
        emb.add_field(name='Modules Loaded', value=len(self.bot.modules))
        emb.add_field(name='Members Seen', value=len(list(self.bot.get_all_members())))
        emb.add_field(name='Channels', value=ch_fmt.format(*[str(i) for i in chlist]))
        emb.add_field(name='Custom Emojis', value=len(list(self.bot.get_all_emojis())))
        emb.add_field(name='Commands', value=str(len(self.bot.commands)))
        emb.add_field(name='ID', value=target.id)
        emb.add_field(name='Invite Link', value='https://tiny.cc/goldbot')
        await self.bot.say(home_broadcast, embed=emb)

    @commands.command(pass_context=True, aliases=['embedhelp', 'embedshelp', 'emhelp', 'ebhelp', 'embhelp', 'pembedhelp', 'pembedshelp', 'pemhelp', 'pebhelp', 'pembhelp', 'pehelp'])
    async def ehelp(self, ctx, *commands: str):
        """Shows an experimental embed-based help.
        Usage: ehelp"""
        if ctx.invoked_with.startswith('p'):
            await or_check_perms(ctx, ['bot_admin', 'manage_server', 'manage_messages', 'manage_channels'])
        pages = self.bot.formatter.eformat_help_for(ctx, self.bot)
        target = self.bot.user
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        if len(pages) > 1:
            destination = ctx.message.author
        else:
            destination = ctx.message.channel
        if ctx.invoked_with.startswith('p'):
            destination = ctx.message.channel
        for page in pages:
            await self.bot.send_message(destination, embed=page)
        if destination == ctx.message.author:
            await self.bot.say(ctx.message.author.mention + ' **__I\'ve private messaged you my help, please check your DMs!__**')

    @commands.cooldown(1, 9.5, type=commands.BucketType.server)
    @commands.command(pass_context=True, aliases=['ping', 'pong', 'delay', 'net', 'network', 'lag', 'netlag'])
    async def latency(self, ctx):
        """Get the current network latency to Discord.
        Usage: latency"""
        begin_time = datetime.now()
        msg = await self.bot.say('Getting latency... `0`')
        for i in range(3):
            await self.bot.edit_message(msg, 'Getting latency... `%s`' % str(i + 1))
        time_diff = datetime.now() - begin_time
        await self.bot.edit_message(msg, 'Latency is: %sms.' % str(round((time_diff.total_seconds() / 4) * 1000, 2)))

    @commands.command(pass_context=True, aliases=['ram', 'memory', 'usage', 'mem', 'musage'])
    async def uptime(self, ctx):
        """Report the current uptime of the bot.
        Usage: uptime"""
        up = await self.bot.format_uptime()
        ram = await self.bot.get_ram()
        got_conversion = ram[0]
        ram_final = (' RAM usage is **' + str(round(ram[1], 1)) + ' MB (%s MiB)**.' % str(round(ram[2], 1))) if got_conversion else ''
        await self.bot.say(ctx.message.author.mention + ' I\'ve been up for **' + up + '**.' + ram_final)

    @commands.command(pass_context=True, aliases=['link', 'invlink', 'addbot', 'botadd'])
    async def invite(self, ctx, *rids: str):
        """Generate an invite link for myself or another bot.
        Usage: invite {optional: bot ids}"""
        ids = list(rids)
        msg = []
        if not ids:
            ids.append(self.bot.user.id)
        for iid in ids:
            try:
                int(iid)
                if len(iid) == 18:
                    if iid == self.bot.user.id:
                        msg.append('https://discordapp.com/api/oauth2/authorize?client_id={0}&scope=bot&permissions={1} (<https://tiny.cc/goldbot> for short)'.format(iid, self.bot.perm_mask))
                    else:
                        msg.append('https://discordapp.com/api/oauth2/authorize?client_id=%s&scope=bot&permissions=502463606' % iid)
                else:
                    msg.append('**Invalid ID **`%s`** (must be 18 numbers)!**' % iid)
            except ValueError:
                msg.append('**Invalid ID **`%s`** (must be made of numbers)!**' % iid)
        if msg:
            await self.bot.say('\n'.join(msg))

    @commands.command(aliases=['homeland', 'web', 'website', 'webpage'])
    async def home(self):
        """Get the link to my homeland.
        Usage: home"""
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
        Usage: poll [emojis] [question] [time in seconds]"""
        async def cem_help(emojis, raw_c_emojis, cem_map, c_emojis):
            """Custom emoji helper."""
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
        try: # UCS-4
            highpoints = re.compile(u'[\U00010000-\U0010ffff\u2615]')
        except re.error: # UCS-2
            highpoints = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
        u_emojis = re.findall(highpoints, question)
        raw_c_emojis = re.findall(re.compile(r'<:[a-z]+:[0-9]{18}>', flags=re.IGNORECASE), question)
        c_emojis = []
        emojis = u_emojis
        await cem_help(emojis, raw_c_emojis, cem_map, c_emojis)
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
        elif len(emojis) < 2:
            await self.bot.say('**You need at least 2 emojis to poll!**')
            return
        msg_key = ctx.message.author.mention + ' is now polling:\n    \u2022 ' + question + '\n'
        msg = await self.bot.say(msg_key + '**POLL NOT ACTIVE YET, ADDING REACTIONS.**')
        for emoji in emojis:
            await self.bot.add_reaction(msg, emoji)
            await asyncio.sleep(0.14)
        await self.bot.edit_message(msg, msg_key + '**POLL IS NOW ACTIVE. Give it a vote!**')
        emojis = list(emojis)
        poll_table = OrderedDict((str(i), []) for i in emojis)
        task = self.loop.create_task(self.poll_task(emojis, msg, poll_table))
        await asyncio.sleep(stime)
        task.cancel()
        _vote_table = {i: len(poll_table[i]) for i in poll_table}
        vote_table = OrderedDict(reversed(sorted(_vote_table.items(), key=lambda t: t[1])))
        _totals = '\n'.join([str(i) + ': {0} votes'.format(str(vote_table[i])) for i in vote_table])
        winner = max(vote_table, key=vote_table.get)
        await self.bot.say('**Poll time is over, stopped! Winner is...** ' + str(winner) + '\nResults were:\n' + _totals)
        await self.bot.edit_message(msg, msg_key + '**POLL HAS ALREADY FINISHED.**')
        #await self.bot.say('VT `' + str(vote_table) + '`')

    @commands.command(aliases=['sw'], pass_context=True)
    async def stopwatch(self, ctx):
        """A stopwatch for your convenience."""
        author = ctx.message.author
        if not author.id in self.stopwatches:
            self.stopwatches[author.id] = int(time.perf_counter())
            await self.bot.say(author.mention + ' Stopwatch started!')
        else:
            tmp = abs(self.stopwatches[author.id] - int(time.perf_counter()))
            tmp = str(timedelta(seconds=tmp))
            await self.bot.say(author.mention + ' Stopwatch stopped! Time: **' + tmp + '**')
            self.stopwatches.pop(author.id, None)

    @commands.command(pass_context=True, name='id', aliases=['myid', 'sid', 'serverid'])
    async def _id(self, ctx):
        """Get all the current scope IDs."""
        fmt = '''**ID Party!**
Server ID: `{0.server.id}` (same as default channel ID and @\u200beveryone role ID!)
Channel ID: `{0.channel.id}`
Your ID: `{0.author.id}`
Server Owner\'s ID: `{0.server.owner.id}`
**You can also look up the ID of other people with** `{1.prefix}user [name / id / mention]`**.**'''
        await self.bot.say(fmt.format(ctx.message, ctx))

    @commands.group(pass_context=True, no_pm=True, aliases=['cleverbutts', 'cbs'])
    async def cleverbutt(self, ctx):
        """Manage Cleverbutt stuff.
        Usage: cleverbutt [subcommand] {arguments}"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @cleverbutt.command(pass_context=True, no_pm=True, name='start', aliases=['kickstart'])
    async def cleverbutt_kickstart(self, ctx, *msg: str):
        """Kickstart / start cleverbutts conversation
        Usage: cleverbutt start {optional: message}"""
        await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages'])
        c_map = {c.name: c for c in ctx.message.server.channels}
        if 'cleverbutts' in c_map:
            ch = c_map['cleverbutts']
            if msg:
                await self.bot.send_message(ch, ctx.raw_args)
            else:
                await self.bot.send_message(ch, 'Hello, what\'re you up to?')
            await self.bot.say('**Message sent in <#%s>!**' % str(ch.id))
        else:
            await self.bot.say('**There\'s no** `#cleverbutts` **channel in this server!**')

    @commands.command(pass_context=True, aliases=['memegen'])
    async def meme(self, ctx, *, pre_text: str):
        """Generate a meme!
        Usage: meme [top text] [bottom text]"""
        char_table = {
            '-': '--',
            '_': '__',
            '?': '~q',
            '%': '~p',
            '#': '~h',
            '/': '~s',
            '"': "''",
            '\n': ' '
        }
        for key in char_table:
            pre_text = pre_text.replace(key, char_table[key])
        pre_text = pre_text.replace('    ', '__bottom__')
        pre_text = pre_text.replace(' ', '-')
        if '__bottom__' in pre_text:
            segments = pre_text.split('__bottom__')
        else:
            segments = textwrap.wrap(pre_text, width=int(len(pre_text) / 2))
        async with aiohttp.ClientSession(loop=asyncio.get_event_loop()) as session:
            with async_timeout.timeout(10):
                async with session.get('https://memegen.link/api/templates/') as r:
                    rtext = await r.text()
                    templates = list(json.loads(rtext).values())
                rtemp = random.choice(templates)
                meme_url = rtemp + '/' + segments[0] + '/' + segments[1] + '.jpg'
                async with session.get(meme_url) as r:
                    raw_image = await r.read()
        await self.bot.send_file(ctx.message.channel, fp=BytesIO(raw_image), filename='meme.jpg')

    @commands.command(pass_context=True, aliases=['statistics', 'servers', 'channels', 'members', 'users', 'seen'])
    async def stats(self, ctx):
        """Dump some of my stats. Full version = info command.
        Usage: stats"""
        fmt = '''{0.author.mention} Here are my stats: (get even more with `{1}info`!)
**Servers**: {2}
**Channels**: {3}
**Members**: {4}
**Uptime**: {5}
**Lines of Code**: {6}'''
        up = await self.bot.format_uptime()
        await self.bot.say(fmt.format(ctx.message, ctx.prefix, str(len(self.bot.servers)), str(len(list(self.bot.get_all_channels()))), str(len(list(self.bot.get_all_members()))), up, str(self.bot.lines)))

    @commands.command(aliases=['randcolor', 'randc', 'rc', 'randomcolor', 'colorgen', 'gcolor', 'gencolor'])
    async def rcolor(self):
        """Generate a random color.
        Usage: rcolor"""
        col_rgb = [random.randint(1, 255) for i in range(0, 3)]
        col_str = '0x%02X%02X%02X' % (col_rgb[0], col_rgb[1], col_rgb[2])
        await self.bot.say(embed=discord.Embed(color=int(col_str, 16), title='Hex: ' + col_str.replace('0x', '#') + ' | RGB: ' + ', '.join([str(c) for c in col_rgb])))

    @commands.command(aliases=['character', 'char', 'cinfo', 'unicode', 'uinfo'])
    async def charinfo(self, *, uchars: str):
        """Get the Unicode info for a character or characters.
        Usage: charinfo [character(s)]"""
        no_preview = [
            '\u0020',
            '\uFEFF'
        ]
        cinfo = commands.Paginator(prefix='', suffix='')
        for char in list(uchars.replace('\n', '')):
            hexp = str(hex(ord(char))).replace('0x', '').upper()
            while len(hexp) < 4:
                hexp = '0' + hexp
            preview = f' (`{char}`)'
            cinfo.add_line(f'U+{hexp} {unicodedata.name(char)} {char}' + (preview if char not in no_preview else ''))
        for page in cinfo.pages:
            await self.bot.say(page)

    @commands.command()
    async def encode(self, *, content: str):
        """Encode your text into Goldmine's encoding!
        Usage: encode [text]"""
        await self.bot.say('```' + (await b_encode(content)) + '```')
    @commands.command()
    async def decode(self, *, content: str):
        """Decode your text from Goldmine's encoding!
        Usage: decode [encoded text]"""
        await self.bot.say('```' + (await b_decode(content)) + '```')
    @commands.command()
    async def fakecode(self, *, content: str):
        """Fake encoding for Goldmine's encoding. Not secure at all.
        Usage: fakecode [text]"""
        await self.bot.say('```' + ('d1;g4.4689257;l0&' + ('@'.join([str(ord(c)) for c in content])) + '~51@77@97@105@110@83@104@105@102@116@67@111@114@114@101@99@116') + '```')

    @commands.command(pass_context=True, aliases=['mc'])
    async def minecraft(self, ctx, *, server_ip: str):
        """Get information about a Minecraft server.
        Usage: minecraft [server address]"""
        port = 25565
        port_split = server_ip.split(':')
        server = port_split[0].replace('/', '')
        if len(port_split) > 1:
            try:
                port = int(port_split[1])
            except ValueError:
                pass
        try:
            self.logger.info('Connecting to Minecraft server ' + server + ':' + str(port) + '...')
            with async_timeout.timeout(5):
                data = await self.loop.run_in_executor(None, mclib.get_info, server, port)
        except Exception as e:
            await self.bot.send_message(ctx.message.channel, f':warning: Couldn\'t get server info for `{server}:{port}`.')
            return
        desc = ''
        server_type = 'Vanilla'
        def decode_extra_desc():
            final = []
            format_keys = {
                'bold': '**',
                'italic': '*',
                'underlined': '__',
                'strikethrough': '~~'
            }
            for e in data['description']['extra']:
                item = e['text']
                for fkey in format_keys:
                    if e.get(fkey, False): 
                        int_key = '%{f:' + fkey + '}$'
                        item = int_key + item + int_key
                final.append(item)
            final = ''.join(final)
            for fkey in format_keys:
                int_key = '%{f:' + fkey + '}$'
                final = final.replace(int_key * 3, '').replace(int_key * 2, '')
                final = final.replace(int_key, format_keys[fkey])
            return final
        if isinstance(data['description'], dict):
            if 'text' in data['description']:
                if data['description']['text']:
                    desc = data['description']['text']
                else:
                    desc = decode_extra_desc()
            else:
                desc = decode_extra_desc()
        elif isinstance(data['description'], str):
            desc = data['description']
        else:
            desc = str(data['description'])
        def decode_section_code():
            formats = {
                'l': '**',
                'n': '__',
                'o': '*',
                'k': '',
                'm': '~~',
                'k': '**',
                'r': ''
            } # k = obf, r = reset
            state = ''
        desc = re.sub(r'\u00a7[4c6e2ab319d5f780lnokmr]', '', desc)
        rc = int('0x%06X' % random.randint(0, 256**3-1), 16)
        emb = discord.Embed(title=server + ':' + str(port), description=desc, color=rc)
        try:
            target = ctx.message.server.me
        except AttributeError:
            target = self.bot.user
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        emb.set_footer(text=target.name, icon_url=avatar_link)
        emb.add_field(name='Players', value=str(data['players']['online']) + '/' + str(data['players']['max']))
        if 'sample' in data['players']:
            if data['players']['sample']:
                emb.add_field(name='Players Online', value=smartjoin([p['name'] for p in data['players']['sample']]))
        emb.add_field(name='Version', value=re.sub(r'\u00a7[4c6e2ab319d5f78lnokmr]', '', data['version']['name']))
        emb.add_field(name='Protocol Version', value=data['version']['protocol'])
        if 'modinfo' in data:
            if 'modList' in data['modinfo']:
                if data['modinfo']['modList']:
                    emb.add_field(name='Mods', value=smartjoin([m['modid'].title() + ' ' +
                                  m['version'] for m in data['modinfo']['modList']]))
                else:
                    emb.add_field(name='Use of Mods', value='This server appears to fake its identity, so Forge clients will send their mod list.')
            if 'type' in data['modinfo']:
                if data['modinfo']['type']:
                    t = data['modinfo']['type']
                    if t.lower() == 'fml':
                        server_type = 'Forge / FML'
                    else:
                        server_type = t.title()
        emb.add_field(name='Server Type', value=server_type)
        await self.bot.say(embed=emb)

    @commands.command()
    async def contact(self, *, message: str):
        """Contact the bot owner with a message.
        Usage: contact [message]"""
        with open(os.path.join('data', 'contact.txt'), 'a') as f:
            f.write(message + '\n')
        await self.bot.say(':thumbsup: Message recorded.')

def setup(bot):
    c = Utility(bot)
    bot.add_cog(c)
