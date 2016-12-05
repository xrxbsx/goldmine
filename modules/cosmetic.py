"""Definition of the bot's Cosmetic module.'"""
import asyncio
import random
import discord
from discord.ext import commands
import util.datastore as store
import util.ranks as rank
from .cog import Cog
from util.const import charsets

class Cosmetic(Cog):
    """Commands for some neat-o fun!
    Includes color changing and more.
    """

    def __init__(self, bot):
        self.al_aliases = [key for key in charsets]
#        print(self.al_aliases)
        super().__init__(bot)

    @commands.command(aliases=['color'])
    async def role(self, role: str):
        """Set a public role on your account.
        Syntax: role|color [role name]"""
        await self.bot.say('Role setting is not implemented yet!')

    @commands.command(pass_context=True, aliases=['xp', 'level', 'lvl', 'exp', 'levels'])
    async def rank(self, ctx):
        """Check your experience, level, and rank!
        Syntax: xp|rank|level|lvl|exp|levels"""
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

    @commands.command(pass_context=True)
    async def emotes(self, ctx):
        """Lists all the current custom emoji on this server.
        Syntax: emotes"""
        cemotes = ctx.message.author.server.emojis
        em_string = (' '.join([str(i) for i in cemotes]) if len(cemotes) >= 1 else 'This server has no custom emojis!')
        await self.bot.say(' '.join(em_string))

    @commands.command(pass_context=True)
    async def etest(self, ctx):
        """Test custom rich embeds.
        Syntax: etest"""
        embed_data = {
            'title': 'This is the title',
            'description': '''This is the description
Testing multi line
cool right?''',
            'color': int('0x%06X' % random.randint(0, 256**3-1), 16)
        }
        r_embed = discord.Embed(**embed_data)
        r_embed.set_thumbnail(url='https://discordapp.com/api/guilds/245387841432059904/icons/305ad4227eec49760731f38117c49af6.jpg') #top right
        r_embed.set_image(url='https://discordapp.com/api/guilds/250304680159215616/icons/7d1bb7b626b7bdf15b838288fc6ed346.jpg') #bottom
        r_embed.set_footer(text='Hi this is the footer text', icon_url='https://images.discordapp.net/icons/239772188649979904/b5a73c73e291e059a6bebdc9b98c6f89.jpg')
        r_embed.set_author(name='Name Hi this is the header text / author', url='http://khronodragon.com', icon_url='https://images.discordapp.net/icons/239772188649979904/b5a73c73e291e059a6bebdc9b98c6f89.jpg')
        for i in range(1, 18):
            icount = 1
            r_embed.add_field(name='Field ' + str(i), value='Test value for ' + str(i), inline=False)
            r_embed.add_field(name='Field ' + str(i) + '.' + str(icount) + 'i', value='Test value for ' + str(i), inline=True)
            icount += 1
            r_embed.add_field(name='Field ' + str(i) + '.' + str(icount) + 'i', value='Test value for ' + str(i), inline=True)
            icount += 1
            r_embed.add_field(name='Field ' + str(i) + '.' + str(icount) + 'i', value='Test value for ' + str(i), inline=True)
            icount += 1
            r_embed.add_field(name='Field ' + str(i), value='Test value for ' + str(i), inline=False)
            icount = 1
        await self.bot.send_message(ctx.message.channel, embed=r_embed)

    @commands.command(aliases=['rev', 'mirror'])
    async def reverse(self, *rmsg):
        await self.bot.say(':repeat: ' + ' '.join(rmsg)[::-1])

    @commands.command(pass_context=True, aliases=['math_sans_italic', 'circled', 'math_double', 'math_bold_italic', 'math_sans_bold_italic', 'parenthesized', 'math_bold_fraktur', 'math_sans_bold', 'squared', 'math_mono', 'fullwidth', 'squared_negative', 'normal', 'circled_negative', 'regional', 'math_sans', 'math_bold_script', 'math_bold'])
    async def style(self, ctx, *rmsg):
        """Stylize text in cool alphabets! Invoke with alphabet name.
        Syntax: style [style name] [text here]"""
        if rmsg:
            imsg = ' '.join(rmsg)
            final_result = await self.stylize(ctx.invoked_with.lower(), imsg)
            await self.bot.say(final_result)
        else:
            await self.bot.say('You must invoke this command as: `[p][name of set] [message here]`.** For example: `!math_bold hello world`! Here are the character sets available:')
            await self.fontlist.invoke(ctx)

    async def stylize(self, alphabet, intxt):
        char_rep = []
        final_result = ''
        for i in list(intxt):
            c_index = list(charsets['normal']).index(i)
            char_rep.append(c_index)
        for i in char_rep:
            final_result += charsets[alphabet][i]
        return final_result

    @commands.command(aliases=['fonts', 'list', 'alphabet', 'alphabets', 'alphalist', 'styles', 'stylelist', 'chars', 'charlist', 'charsets', 'charsetlist'])
    async def fontlist(self):
        """List the available fancy character sets / alphabets / fonts.
        Syntax: fonts|fontlist|alphabets|styles"""
        pager = commands.Paginator(prefix='', suffix='')
        pager.add_line('**Listing all character sets defined with samples.**')
        for i in self.al_aliases:
            tmp = await self.stylize(i, 'abcdefghijklmnopqrstuvwxyz')
            pager.add_line('**{0}**: `{1}`'.format(i, tmp))
        pager.add_line('**Invoke with `[p][name of set] [message here]`.** For example: `!math_bold hello world`.')
        for page in pager.pages:
            await self.bot.say(page)
