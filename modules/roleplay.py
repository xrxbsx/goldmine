"""Definition of the bot's Roleplay module."""
import asyncio
import random
import math
import time
from collections import OrderedDict

import discord
from discord.ext import commands
from pykemon.api import get as pokeget
from pykemon import ResourceNotFoundError
from pykemon.request import _request, Description

import util.datastore as store
import util.quote as quote
from util.perms import check_perms, echeck_perms
from util.const import *

from .cog import Cog


class Roleplay(Cog):
    """Commands related to roleplay.
    Examples: poking, stabbing, and color roles.
    """

    def __init__(self, bot):
        super().__init__(bot)

    @commands.command(pass_context=True, name='rmember', aliases=['randmember', 'randommember', 'randmem', 'rmem'])
    async def rand_member(self, ctx):
        """Choose a random member from the message's server."""
        satisfied = False
        m_list = [i[1] for i in list(enumerate(ctx.message.server.members))]
        while not satisfied:
            rmem = random.choice(m_list)
            satisfied = bool(str(rmem.status) == 'online')
        await ctx.bot.say(rmem.mention)
        return rmem

    @commands.command(pass_context=True, aliases=['boop', 'poke', 'hit'])
    async def slap(self, ctx, target: str):
        """Slaps someone like a boss, for the win.
        Syntax: slap [person]"""
        cmdfix = await store.get_cmdfix(ctx.message.content)
        keystr = '* ' + ctx.message.content.split(' ')[0].strip(cmdfix) + 's *'
        await self.bot.say('*' + ctx.message.author.display_name + keystr +
                           target + '* **' + random.choice(adjs) + '**.')

    @commands.command(pass_context=True, aliases=['stab', 'kill', 'punch', 'shoot', 'hurt', 'fight'])
    async def attack(self, ctx, target: str):
        """Hurts someone with determination in the shot.
        Syntax: attack [person]"""
        await self.bot.say('*' + ctx.message.author.display_name + '* ' +
                           random.choice(fights).format(target) + '. '
                           + random.choice(death).format(target))

    @commands.command()
    async def charlie(self, *args):
        """Ask a question... Charlie Charlie are you there?
        Syntax: charlie [question to ask, without punctuation]"""
        istr = ' '.join(args)
        aq = '' if istr.endswith('?') else '?'
        await self.bot.say('*Charlie Charlie* ' + istr + aq + "\n**" +
                           random.choice(['Yes', 'No']) + '**')

    @commands.command(pass_context=True)
    async def mentionme(self, ctx):
        """Have the bot mention yourself. Useful for testing.
        Syntax: mentionme"""
        await self.bot.say('Hey there, ' + ctx.message.author.mention + '!')

    @commands.command(pass_context=True)
    async def mention(self, ctx, target: discord.Member):
        """Make the bot mention someone. Useful for testing.
        Syntax: mention [mention, nickname, DiscordTag, or username]"""
        await self.bot.say('Hey there, ' + target.mention + '!')

    @commands.command(aliases=['emote', 'csay'])
    async def emotisay(self, *args):
        """Make the bot mention someone. Useful for testing.
        Syntax: emotisay [your text here]"""
        chars = list(' '.join(args).lower())
        cmap = {
            ' ': '    ',
            '#': ':hash:',
            '!': ':exclamation:',
            '?': ':question:',
            '$': ':heavy_dollar_sign:',
            '-': ':heavy_minus_sign:',
            '.': ':small_blue_diamond:',
            '~': ':wavy_dash:',
            '0': ':zero:',
            '1': ':one:',
            '2': ':two:',
            '3': ':three:',
            '4': ':four:',
            '5': ':five:',
            '6': ':six:',
            '7': ':seven:',
            '8': ':eight:',
            '9': ':nine:'
        }
        for i, s in enumerate(chars):
            if s in list('abcdefghijklmnopqrstuvwxyz'):
                chars[i] = ':regional_indicator_' + s + ':'
            if s in cmap:
                chars[i] = cmap[s]
        await self.bot.say(str(''.join(chars)))

    @commands.command(aliases=['cb', 'ask', 'ai', 'bot'])
    async def cleverbot(self, *args):
        """Queries the Cleverbot service. Because why not.
        Syntax: cleverbot [message here]"""
        reply_bot = await self.bot.askcb(' '.join(args))
        await self.bot.say(reply_bot)

    @commands.command(aliases=['randquote', 'getquote'])
    async def quote(self, *args):
        """References a quote from the quote collection.
        Syntax: quote {optional: quote number}"""
        temp_ref = await store.dump()
        try:
            qindx = args[0]
        except IndexError:
            qindx = random.randint(1, temp_ref['quotes'].__len__())
        qindex = int(qindx)
        try:
            out_msg = await quote.qrender(temp_ref['quotes'][qindex - 1], qindex - 1)
        except IndexError:
            out_msg = 'That quote does not exist, try again!'
        await self.bot.say(out_msg)

    @commands.command(aliases=['quotes', 'listquote', 'quoteslist', 'listquotes', 'dumpquotes', 'quotedump', 'quotesdump'])
    async def quotelist(self):
        """Lists all the quotes found in the quote collection.
        Syntax: quotelist"""
        # maybe PM this
        rstore = await store.dump()
        pager = commands.Paginator(prefix='', suffix='')
        pager.add_line('**Listing all quotes defined.**')
        for n, i in enumerate(rstore['quotes']):
            qout = await quote.qrender(i, n)
            pager.add_line(qout)
        for page in pager.pages:
            await self.bot.say(page)

    @commands.command(pass_context=True, aliases=['newquote', 'quotenew', 'addquote', 'makequote', 'quotemake', 'createquote', 'quotecreate'])
    async def quoteadd(self, ctx, *args):
        """Add a quote to the quote collection.
        Syntax: quoteadd [text here]"""
        if args:
            fmt_time = [int(i) for i in time.strftime("%m/%d/%Y").split('/')]
            bname = await store.get_prop(ctx.message, 'bot_name')
            q_template = {
                'id': 0,
                'quote': 'The bot has encountered an internal error.',
                'author': bname,
                'author_ids': [self.bot.user.id],
                'date': fmt_time
            }
            mauthor = ctx.message.author
            q_template['quote'] = ' '.join(args)
            q_template['author'] = mauthor.display_name
            if mauthor.display_name != mauthor.name:
                q_template['author'] += ' (' + mauthor.name + ')'
            q_template['author_ids'] = [mauthor.id]
            rstore = await store.dump()
            q_template['id'] = len(rstore['quotes']) # +1 for next id, but len() counts from 1
            rstore['quotes'].extend([q_template])
            await store.write(rstore)
            await self.bot.say('The quote specified has been successfully added!')
        else:
            await self.bot.say(ctx.message.author.mention + ' You need to specify some text to add!')

    @commands.command(pass_context=True, aliases=['rnewquote', 'rquotenew', 'raddquote', 'rmakequote', 'rquotemake', 'rcreatequote', 'rquotecreate', 'raq'])
    async def rquoteadd(self, ctx, target: discord.Member, *args):
        """Add a quote to the quote collection.
        Syntax: rquoteadd [member] [text here]"""
        await echeck_perms(ctx, ['bot_admin'])
        if args:
            fmt_time = [int(i) for i in time.strftime("%m/%d/%Y").split('/')]
            bname = await store.get_prop(ctx.message, 'bot_name')
            q_template = {
                'id': 0,
                'quote': 'The bot has encountered an internal error.',
                'author': bname,
                'author_ids': [self.bot.user.id],
                'date': fmt_time
            }
            mauthor = target
            q_template['quote'] = ' '.join(args)
            q_template['author'] = mauthor.display_name
            if mauthor.display_name != mauthor.name:
                q_template['author'] += ' (' + mauthor.name + ')'
            q_template['author_ids'] = [mauthor.id]
            rstore = await store.dump()
            q_template['id'] = len(rstore['quotes']) # +1 for next id, but len() counts from 1
            rstore['quotes'].extend([q_template])
            await store.write(rstore)
            await self.bot.say('The quote specified has been successfully added!')
        else:
            await self.bot.say(ctx.message.author.mention + ' You need to specify some text to add!')

    @commands.command(pass_context=True, aliases=['quoteedit', 'modquote', 'editquote'])
    async def quotemod(self, ctx, qindex1: int, *qraw):
        """Modifies an existing quote.
        Syntax: quotemod [quote number] [new text here]"""
        if qraw:
            rstore = await store.dump()
            try:
                q_template = rstore['quotes'][qindex1 - 1]
            except IndexError:
                await self.bot.say(ctx.message.author.mention + ' That quote doesn\'t already exist, maybe create it?')
                return
            mauthor = ctx.message.author
            q_template['quote'] = ' '.join(qraw)
            if mauthor.id not in q_template['author_ids']:
                q_template['author'] += ', ' + mauthor.display_name
                if mauthor.display_name != mauthor.name:
                    q_template['author'] += ' (' + mauthor.name + ')'
            q_template['author_ids'].extend([mauthor.id])
            q_template['date'] = [int(i) for i in time.strftime("%m/%d/%Y").split('/')]
            rstore = await store.dump() # keep store as fresh as possible
            rstore['quotes'][qindex1 - 1] = q_template
            await store.write(rstore)
            await self.bot.say('The quote specified has been successfully modified!')
        else:
            await self.bot.say(ctx.message.author.mention + ' You can\'t empty an existing quote!')

    @commands.command(pass_context=True, aliases=['rmquote', 'quoterm', 'delquote'])
    async def quotedel(self, ctx, qindex: int):
        """Deletes an existing quote. You may only delete your own quotes unless you are the bot owner.
        Syntax: quotedel [quote number]"""
        rstore = await store.dump()
        try:
            q_target = rstore['quotes'][qindex - 1]
        except IndexError:
            await self.bot.say(ctx.message.author.mention + ' That quote doesn\'t already exist, maybe create it for deletion? :stuck_out_tongue:')
            return
        mauthor = ctx.message.author
        _pcheck = await check_perms(ctx, ['bot_owner'])
        if (mauthor.id == q_target['author_ids'][0]) or (_pcheck):
            rstore = await store.dump() # keep store as fresh as possible
            del rstore['quotes'][qindex - 1]
            await store.write(rstore)
            await self.bot.say('The quote specified has been successfully deleted!')
        else:
            await self.bot.say('The quote specified could not be deleted because you do not own it, and are not the bot owner. Sorry!')

    @commands.command(pass_context=True, aliases=['gif', 'soontm', 'tm'])
    async def soon(self, ctx):
        """Feel the loading of 10000 years, aka Soon™.
        Syntax: soon"""
        with open('assets/soon.gif', 'rb') as image:
            await self.bot.send_file(ctx.message.channel, image, filename='soon.gif')

    @commands.command(pass_context=True, aliases=['wface', 'weirdface', 'weird', 'weird_face', 'mystery', 'neato', 'neat', 'random'])
    async def face(self, ctx):
        """Give you a random face. Because really, why not?
        Syntax: face"""
        await self.bot.send_message(ctx.message.channel, random.choice(weird_faces))

    @commands.command(pass_context=True)
    async def emotispam(self, ctx):
        """Spam some emotes! WARNING: Lag alert.
        Syntax: emotispam"""
        await echeck_perms(ctx, ['bot_admin'])
        _em = emojis
        r = list(range(1, math.ceil(len(emojis) / 2000)))
        print('r ' + str(r))
        for i in r:
            print('i ' + str(i))
            await self.bot.say(_em[:2000])
            print('PRE EM ' + _em[:2000])
            _em = _em[2000:]
            print('POST EM ' + _em)

    @commands.command(pass_context=True, aliases=['pokeball', 'pokedex'])
    async def pokemon(self, ctx, *pokemon_name: str):
        """Get the info about a Pokémon!
        Syntax: pokemon|pokedex [name or id]"""
        bot = self.bot
        d_lines = []
        try:
            p_name = pokemon_name[0]
        except IndexError:
            p_name = None
        if p_name:
            try:
                target = await pokeget(pokemon=p_name.lower())
            except ResourceNotFoundError:
                try:
                    target = await pokeget(pokemon_id=int(p_name))
                except (ResourceNotFoundError, ValueError):
                    await bot.say('No such **pokemon**! Try a **Pokédex entry**. (Needs to be **name** or **ID**.)')
                    return
        else:
            count = 709 # current count of pokemon
            target = await pokeget(pokemon_id=random.randint(1, count))
        try:
            fn_point = target.descriptions[target.name.lower() + '_gen_1']
        except KeyError:
            fn_point = random.choice(list(target.descriptions.values()))
        desc_json = await _request('http://pokeapi.co' + fn_point)
        desc = Description(desc_json)
        em_data = {
            'title': target.name.replace('-', ' '),
            'color': int('0x%06X' % random.randint(0, 256**3-1), 16)
        }
        essentials = ['Description', 'National ID', 'Health', 'Height', 'Weight', 'Attack', 'Defense', 'Type(s)']
        skipped = ['Moves', 'Effort Value Yield', 'Egg Groups', 'Total', 'Growth Rate', 'Catch Rate', 'Male-Female Ratio', 'Egg Cycles']
        beginning = ['Description', 'National ID', 'Health', 'Attack', 'Defense', 'Weight', 'Height', 'Speed', 'Special Attack', 'Special Defense', 'Experience', 'Happiness', 'Abilities']
        tw_float = float(target.weight) / 10.0
        th_float = float(target.height) / 10.0
        th_inch = th_float / .3048 % 1 * 12
        em_field_data = {
            'Description': desc.description,
            'National ID': target.id,
            'Health': str(target.hp) + ' HP',
            'Moves': ', '.join(target.moves),
            'Types(s)': ', '.join([i.title() for i in target.types]),
            'Abilities': ', '.join([i.title() for i in target.abilities]),
            'Height': str(th_float) + ' m (' + str(int(math.floor(th_inch / 12))) + ' ft ' + str(round(th_inch % 12, 2)) + ' in)',
            'Weight': str(tw_float) + ' kg (' + str(round(tw_float * 2.2, 2)) + ' lb)',
            'Growth Rate': target.growth_rate,
            'Defense': target.defense,
            'Attack': target.attack,
            'Experience': target.exp,
            'Happiness': target.happiness,
            'Egg Cycles': target.egg_cycles,
            'Catch Rate': target.catch_rate,
            'Special Attack': target.sp_atk,
            'Special Defense': target.sp_def,
            'Speed': target.speed,
            'Total': target.total,
            'Effort Value Yield': target.ev_yield,
            'Male-Female Ratio': target.male_female_ratio,
            'Egg Groups': ', '.join(target.egg_groups)
        }
        em_fields = OrderedDict(sorted(em_field_data.items(), key=lambda t: len(t[0])))
        if target.species:
            em_fields['Species'] = target.species
        if target.evolutions:
            em_fields['Evolves Into'] = ', '.join(target.evolutions)
            em_fields.move_to_end('Evolves Into', last=False)
        for i in reversed(beginning):
            em_fields.move_to_end(i, last=False)
        for key, value in em_fields.items():
            if key not in skipped:
                if key not in essentials:
                    d_lines.append(key + ': ' + str(value))
        emb = discord.Embed(**em_data, description='\n'.join(d_lines))
        for key, value in em_fields.items():
            if key in essentials:
                emb.add_field(name=key, value=value)
        emb.set_thumbnail(url='http://pokeapi.co/media/img/{0}.png'.format(str(target.id)))
        emb.set_image(url='http://pokeapi.co/media/img/{0}.png'.format(str(target.id)))
        emb.set_author(name=target.name.replace('-', ' '), icon_url='http://pokeapi.co/media/img/{0}.png'.format(str(target.id)))
        await bot.send_message(ctx.message.channel, embed=emb)
