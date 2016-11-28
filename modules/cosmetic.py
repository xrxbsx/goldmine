"""Definition of the bot's Cosmetic module.'"""
import asyncio
import discord
from discord.ext import commands
import util.datastore as store
import util.ranks as rank
from .cog import Cog

class Cosmetic(Cog):
    """Commands for some neat-o fun!
    Includes color changing and more.
    """

    charsets = {
        'normal': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'fullwidth': 'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９～ ｀！＠＃＄％＾＆＊（）－＿＝＋［］｛｝|；：＇＂,＜．＞/？\\',
        'circled': 'ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ0①②③④⑤⑥⑦⑧⑨~ `!@#$%^&⊛()⊖_⊜⊕[]{}⦶;:\'",⧀⨀⧁⊘?⦸',
        'circled_negative': '🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩⓿123456789~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'math_bold': '𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'math_bold_fraktur': '𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅0123456789~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'math_bold_italic': '𝒂𝒃𝒄𝒅𝒆𝒇𝒈𝒉𝒊𝒋𝒌𝒍𝒎𝒏𝒐𝒑𝒒𝒓𝒔𝒕𝒖𝒗𝒘𝒙𝒚𝒛𝑨𝑩𝑪𝑫𝑬𝑭𝑮𝑯𝑰𝑱𝑲𝑳𝑴𝑵𝑶𝑷𝑸𝑹𝑺𝑻𝑼𝑽𝑾𝑿𝒀𝒁0123456789~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'math_bold_script': '𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩0123456789~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'math_double': '𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'math_mono': '𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'math_sans': '𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'math_sans_bold': '𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'math_sans_bold_italic': '𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕0123456789~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'math_sans_italic': '𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡0123456789~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'parenthesized': '⒜⒝⒞⒟⒠⒡⒢⒣⒤⒥⒦⒧⒨⒩⒪⒫⒬⒭⒮⒯⒰⒱⒲⒳⒴⒵⒜⒝⒞⒟⒠⒡⒢⒣⒤⒥⒦⒧⒨⒩⒪⒫⒬⒭⒮⒯⒰⒱⒲⒳⒴⒵0⑴⑵⑶⑷⑸⑹⑺⑻⑼~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'regional': '🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿0123456789~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\',
        'squared': '🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉0123456789~ `!@#$%^&⧆()⊟_=⊞[]{}|;:\'",<⊡>⧄?⧅',
        'squared_negative': '🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉0123456789~ `!@#$%^&*()-_=+[]{}|;:\'",<.>/?\\'
    }

    def __init__(self, bot):
        self.al_aliases = [key for key in self.charsets]
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
cool right?'''
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
        Syntax: [style name] [text here]"""
        imsg = ' '.join(rmsg)
        final_result = await self.stylize(ctx.invoked_with.lower(), imsg)
        await self.bot.say(final_result)

    async def stylize(self, alphabet, intxt):
        char_rep = []
        final_result = ''
        for i in list(intxt):
            c_index = list(self.charsets['normal']).index(i)
            char_rep.append(c_index)
        for i in char_rep:
            final_result += self.charsets[alphabet][i]
        return final_result

    @commands.command(aliases=['fonts', 'list', 'alphabet', 'alphabets', 'alphalist', 'styles', 'stylelist', 'chars', 'charlist', 'charsets', 'charsetlist'])
    async def fontlist(self):
        pager = commands.Paginator(prefix='', suffix='')
        pager.add_line('**Listing all character sets defined with samples.**')
        for i in self.al_aliases:
            tmp = await self.stylize(i, 'abcdefghijklmnopqrstuvwxyz')
            pager.add_line('**{0}**: `{1}`'.format(i, tmp))
        pager.add_line('**Invoke with `[p]character_set_name [message here]`.**')
        for page in pager.pages:
            await self.bot.say(page)
