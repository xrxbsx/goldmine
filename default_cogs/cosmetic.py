"""Definition of the bot's Cosmetic module.'"""
from contextlib import suppress
from urllib.parse import urlencode
from .cog import Cog
from util.const import charsets, spinners, lvl_base
import util.dynaimport as di

for mod in ['asyncio', 'random', 'io', 'imghdr', 'aiohttp',
            'async_timeout', 'discord']:
    globals()[mod] = di.load(mod)
json = di.load('util.json')
commands = di.load('util.commands')

class Cosmetic(Cog):
    """Commands for some neat-o fun!
    Includes color changing and more.
    """

    def __init__(self, bot):
        self.al_aliases = [key for key in charsets]
        self.playing_anim = set()
        self.stop_anim = set()
        super().__init__(bot)

    async def on_not_command(self, msg):
        """Table flipping!"""
        if self.bot.selfbot: return
        if msg.author.id != self.bot.user.id:
            if msg.content == '(╯°□°）╯︵ ┻━┻':
                await self.bot.send_message(msg.channel, '┬─┬﻿ ノ( ゜-゜ノ)')

    @commands.command(aliases=['color', 'giveme', 'race'])
    async def role(self, role: str):
        """Set a public role on your account.
        Usage: role [role name]"""
        await self.bot.say('Role setting is not implemented yet!')

    @commands.command(pass_context=True)
    async def emotes(self, ctx):
        """Lists all the current custom emoji on this server.
        Usage: emotes"""
        cemotes = ctx.message.author.server.emojis
        em_string = (' '.join([str(i) for i in cemotes]) if len(cemotes) >= 1 else 'This server has no custom emojis!')
        await self.bot.say(em_string)

    @commands.command(pass_context=True)
    async def etest(self, ctx):
        """Test custom rich embeds.
        Usage: etest"""
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
        r_embed.set_author(name='Name Hi this is the header text / author', url='https://blog.khronodragon.com/', icon_url='https://images.discordapp.net/icons/239772188649979904/b5a73c73e291e059a6bebdc9b98c6f89.jpg')
        for i in range(1, 4):
            r_embed.add_field(name='Field ' + str(i), value='Test value for ' + str(i), inline=False)
            for icount in range(1, 3):
                r_embed.add_field(name='Field ' + str(i) + '.' + str(icount) + 'i', value='Test value for ' + str(i))
            r_embed.add_field(name='Field ' + str(i), value='Test value for ' + str(i), inline=False)
        await self.bot.say(embed=r_embed)

    @commands.command(aliases=['rev', 'mirror'])
    async def reverse(self, *, rmsg: str):
        """Reverse some text you give.
        Usage: reverse [text here]"""
        await self.bot.say(':repeat: ' + rmsg[::-1])

    @commands.command(pass_context=True, aliases=['math_sans_italic', 'circled', 'math_double', 'math_bold_italic', 'math_sans_bold_italic', 'parenthesized', 'math_bold_fraktur', 'math_sans_bold', 'squared', 'math_mono', 'fullwidth', 'squared_negative', 'normal', 'circled_negative', 'regional', 'math_sans', 'math_bold_script', 'math_bold', 'upside_down'])
    async def style(self, ctx, *rmsg):
        """Stylize text in cool alphabets! Invoke with alphabet name.
        Usage: style [style name] [text here]"""
        if rmsg:
            imsg = ' '.join(rmsg)
            final_result = await self.stylize(ctx.invoked_with.lower(), imsg)
            await self.bot.say(final_result)
        else:
            await self.bot.say('**You must invoke this command as: `[p][name of set] [message here]`.** For example: `!math_bold hello world`! Here are the character sets available:')
            await self.fontlist.invoke(ctx)

    async def stylize(self, alphabet, intxt):
        return intxt.translate(str.maketrans(charsets['normal'], charsets[alphabet]))

    @commands.command(aliases=['fonts', 'list', 'alphabet', 'alphabets', 'alphalist', 'styles', 'stylelist', 'chars', 'charlist', 'charsets', 'charsetlist'])
    async def fontlist(self):
        """List the available fancy character sets / alphabets / fonts.
        Usage: fonts"""
        pager = commands.Paginator(prefix='', suffix='')
        pager.add_line('**Listing all character sets defined with samples.**')
        for i in self.al_aliases:
            print('A ' + i)
            tmp = await self.stylize(i, 'abcdefghijklmnopqrstuvwxyz')
            pager.add_line('**{0}**: `{1}`'.format(i, tmp))
        pager.add_line('**Invoke with `[p][name of set] [message here]`.** For example: `!math_bold hello world`.')
        for page in pager.pages:
            await self.bot.say(page)

    @commands.cooldown(1, 6, type=commands.BucketType.server)
    @commands.command(pass_context=True, aliases=['af', 'sca', 'anim', 'a', 'playanim', 'aplay', 'animplay'])
    async def animation(self, ctx, anim_seq, runs: int):
        """Do a 0.9 fps animation x times from the given sequence.
        Usage: af [packed animation] [number of runs]"""
        try:
            cmid = ctx.message.server.id
        except AttributeError:
            cmid = 'dm' + ctx.message.author.id
        if cmid not in self.playing_anim:
            self.playing_anim.add(cmid)
            msg = await self.bot.say('Starting animation...')
            for _xi in range(runs):
                for frame in anim_seq:
                    if cmid not in self.stop_anim:
                        await self.bot.edit_message(msg, frame)
                        await asyncio.sleep(0.93)
                    else:
                        await self.bot.edit_message(msg, '**Animation stopped!**')
                        await self.bot.say('**Animation stopped!**')
                        self.playing_anim.remove(cmid)
                        return
            await self.bot.edit_message(msg, '**Animation stopped!**')
            await self.bot.say('**Animation stopped!**')
            self.playing_anim.remove(cmid)
        else:
            await self.bot.say('**Already playing an animation in this server!**')

    @commands.command(pass_context=True, aliases=['sa', 'ssca', 'sanim', 'stopanimation', 'animstop', 'saf'])
    async def stopanim(self, ctx):
        """Stop the animation playing in this server, if any.
        Usage: stopanim"""
        try:
            cmid = ctx.message.server.id
        except AttributeError:
            cmid = 'dm' + ctx.message.author.id
        if cmid in self.playing_anim:
            await self.bot.say('**Stopping animation...**')
            self.stop_anim.add(cmid)
            await asyncio.sleep(1.9)
            self.stop_anim.remove(ctmid)
        else:
            await self.bot.say('**Not playing any animation here!**')

    @commands.command(aliases=['lanim', 'listanims', 'listanim', 'animationlist', 'animl', 'anims', 'animations', 'al', 'packs', 'packed', 'pal', 'pa'])
    async def animlist(self):
        """List the packed animations I have saved.
        Usage: animlist"""
        await self.bot.say('**Listing stored packed animations.**```\n' + '\n'.join(spinners) + '```')

    @commands.command(pass_context=True, aliases=['spider', 'spiders'])
    async def webs(self, ctx):
        """Some web developers that like bugs.
        Usage: web"""
        with open('assets/webs.jpeg', 'rb') as image:
            await self.bot.send_file(ctx.message.channel, image, filename='spiders_webs.jpg')

#    @commands.cooldown(1, 4, type=commands.BucketType.user)
    @commands.command(pass_context=True, aliases=['random.cat', 'randomcat', 'rcat', 'cats', 'catrandom', 'random_cat'])
    async def cat(self, ctx):
        """Get a random cat! Because why not.
        Usage: cat"""
        async with aiohttp.ClientSession(loop=self.loop) as session:
            with async_timeout.timeout(8):
                async with session.get('http://random.cat/meow') as response:
                    ret = await response.text()
                try:
                    async with session.get(json.loads(ret)['file']) as resp:
                        img = await resp.read()
                except (KeyError, ValueError, TypeError):
                    await self.bot.say(f'**Failed to get a cat, maybe random.cat is down?**')
                    return
        img_bytes = io.BytesIO(img)
        await self.bot.send_file(ctx.message.channel, img_bytes, filename='random-cat.' + imghdr.what(img_bytes))
    @commands.command(pass_context=True, aliases=['random.dog', 'randomdog', 'rdog', 'dogs', 'dograndom', 'random_dog'])
    async def dog(self, ctx):
        """Get a random dog! Because why not.
        Usage: dog"""
        async with aiohttp.ClientSession(loop=self.loop) as session:
            with async_timeout.timeout(8):
                async with session.get('http://random.dog/woof') as response:
                    ret = await response.text()
                try:
                    async with session.get('http://random.dog/' + ret) as resp:
                        img = await resp.read()
                except (KeyError, ValueError, TypeError):
                    await self.bot.say(f'**Failed to get a cat, maybe random.dog is down?**')
                    return
        img_bytes = io.BytesIO(img)
        await self.bot.send_file(ctx.message.channel, img_bytes, filename='random-dog.' + imghdr.what(img_bytes))

    @commands.command(pass_context=True, aliases=['temote', 'bemote', 'dcemote', 'getemote', 'fetchemote'])
    async def emote(self, ctx, _emote: str):
        """Get a Twitch, FrankerFaceZ, BetterTTV, or Discord emote.
        Usage: emote [name of emote]"""
        emote = _emote.replace(':', '')
        ext = 'png'
        async with aiohttp.ClientSession(loop=self.loop) as session:
            with async_timeout.timeout(13):
                try:
                    async with session.get('https://static-cdn.jtvnw.net/emoticons/v1/' + str(self.bot.emotes['twitch'][emote]['image_id']) + '/1.0') as resp:
                        emote_img = await resp.read()
                except KeyError: # let's try frankerfacez
                    try:
                        async with session.get('https://cdn.frankerfacez.com/emoticon/' + str(self.bot.emotes['ffz'][emote]) + '/1') as resp:
                            emote_img = await resp.read()
                    except KeyError: # let's try BetterTTV
                        try:
                            async with session.get(self.bot.emotes['bttv'][emote]) as resp:
                                emote_img = await resp.read()
                        except KeyError: # let's try Discord
                            await self.bot.say('**No such emote!** I can fetch from Twitch, FrankerFaceZ, BetterTTV, or Discord (soon).')
                            return False
        img_bytes = io.BytesIO(emote_img)
        ext = imghdr.what(img_bytes)
        await self.bot.send_file(ctx.message.channel, img_bytes, filename=f'emote.{ext}')

def setup(bot):
    c = Cosmetic(bot)
    bot.add_cog(c)
