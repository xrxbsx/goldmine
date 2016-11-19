"""Definition of the bot's Roleplay module."""
import random
import time

import discord
from cleverbot import Cleverbot
from discord.ext import commands

import util.datastore as store
import util.quote as quote
from util.perms import check_perms
from properties import bot_name

from .cog import Cog


class Roleplay(Cog):
    """Commands related to roleplay.
    Examples: poking, stabbing, and color roles.
    """
    adjs = [
        'lovingly',
        'lamely',
        'limply',
        'officially',
        'for money',
        'sadly',
        'roughly',
        'angrily',
        'harshly',
        'without hesitation',
        'quickly',
        'greedily',
        'shamefully',
        'dreadfully',
        'painfully',
        'intensely',
        'digitally',
        'unofficially',
        'nervously',
        'invitingly',
        'seductively',
        'embarassingly',
        'thoroughly',
        'doubtfully',
        'proudly'
    ]
    fights = [
        'pokes {0} with a spear',
        'impales {0}',
        'stabs {0}',
        'guts {0} with a stone knife',
        'eviscerates {0} with a sharp stone',
        'decapitates {0} with a wand',
        'fires cruise missle at {0}',
        'backstabs {0}',
        'punches {0}',
        'poisons {0}',
        'opens trapdoor under {0}',
        '360 quick scopes {0}',
        'noscopes {0}',
        'normally snipes {0}',
        'uses katana to slice through {0}',
        'deadly stares at {0}',
        'uses a trebuchet to shoot a 95kb projectile over 300 meters at {0}',
        'snaps neck from {0}',
        'pours lava over {0}',
        'dumps acid above {0}',
        'shoots with a glock 17 at {0}',
        'incinerates {0}',
        'uses a tridagger to stab {0}',
        'assasinates {0}',
        'fires with a minigun at {0}',
        'fires with bazooka at {0}',
        'uses granny bomb at {0}',
        'throws bananabomb at {0}',
        'throws holy grenade at {0}'
    ]
    death = [
        '{0} dies.',
        '{0} survives.',
        'Blood pours from {0}.',
        '{0} heals themself.',
        'Fairies take {0} away.',
        'An old man carries {0} away.',
        '{0} is in shock.',
        '{0} passes out.'
    ]

    def __init__(self, bot, cmdfix, bname):
        self.cb = Cleverbot()
        super().__init__(bot, cmdfix, bname)

    @commands.command(pass_context=True)
    async def poke(self, ctx, target: str):
        """Pokes someone... with random results!
        Syntax: poke [person]"""
        await self.bot.say('*' + ctx.message.author.display_name + '* pokes *' +
                           target + '* **' + random.choice(self.adjs) + '**.')

    @commands.command(pass_context=True)
    async def boop(self, ctx, target: str):
        """Boops someone with possibly satisfying results.
        Syntax: boop [person]"""
        await self.bot.say('*' + ctx.message.author.display_name + '* boops *' +
                           target + '* **' + random.choice(self.adjs) + '**.')

    @commands.command(pass_context=True)
    async def stab(self, ctx, target: str):
        """Floran besst sssstabber! Painful, too.
        Syntax: stab [person]"""
        await self.bot.say('*' + ctx.message.author.display_name + '* ' +
                           random.choice(self.fights).format(target) + '. '
                           + random.choice(self.death).format(target))

    @commands.command(pass_context=True)
    async def attack(self, ctx, target: str):
        """Hurts someone with determination in the shot.
        Syntax: attack [person]"""
        await self.bot.say('*' + ctx.message.author.display_name + '* ' +
                           random.choice(self.fights).format(target) + '. '
                           + random.choice(self.death).format(target))

    @commands.command()
    async def charlie(self, *args):
        """Ask a question... Charlie Charlie are you there?
        Syntax: charlie [question to ask, without punctuation]"""
        await self.bot.say('*Charlie Charlie* ' + ' '.join(args) + "?\n**" +
                           random.choice(['Yes', 'No']) + '**')

    @commands.command(pass_context=True)
    async def mentionme(self, ctx):
        """Have the bot mention yourself. Useful for testing.
        Syntax: mentionme"""
        await self.bot.say('Hey there, ' + ctx.message.author.mention + '!')

    @commands.command(pass_context=True)
    async def mention(self, ctx, target: str):
        """Make the bot mention someone. Useful for testing.
        Syntax: mention [mention, nickname, DiscordTag, or username]"""
        await self.bot.say('Hey there, ' + target + '!')

    @commands.command()
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

    @commands.command()
    async def cleverbot(self, *args):
        """Queries the Cleverbot service. Because why not.
        Syntax: cleverbot [message here]"""
        await self.bot.say(self.cb.ask(' '.join(args)))

    @commands.command()
    async def quote(self, *args):
        """References a quote from the quote store.
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

    @commands.command()
    async def quotelist(self):
        """Lists all the quotes found in the quote store.
        Syntax: quotelist"""
        rstore = await store.dump()
        final_msg = '**Listing all quotes defined.**\n'
        for n, i in enumerate(rstore['quotes']):
            qout = await quote.qrender(i, n)
            final_msg += qout + '\n'
        await self.bot.say(final_msg)

    @commands.command(pass_context=True)
    async def quoteadd(self, ctx, *args):
        """Adds a quote to the quote store.dump
        Syntax: quoteadd [text here]"""
        fmt_time = [int(i) for i in time.strftime("%m/%d/%Y").split('/')]
        q_template = {
            'id': 0,
            'quote': 'The bot has encountered an internal error.',
            'author': bot_name,
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

    @commands.command(pass_context=True)
    async def quotemod(self, ctx, qindex1: int, *qraw):
        """Modifies an existing quote.
        Syntax: quotemod [quote number] [new text here]"""
        rstore = await store.dump()
        q_template = rstore['quotes'][qindex1 - 1]
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

    @commands.command(pass_context=True)
    async def quotedel(self, ctx, qindex: int):
        """Deletes an existing quote. You may only delete your own quotes unless you are the bot owner.
        Syntax: quotedel [quote number]"""
        rstore = await store.dump()
        q_target = rstore['quotes'][qindex - 1]
        mauthor = ctx.message.author
        if (mauthor.id == q_target['author_ids'][0]) or (check_perms(ctx, ['bot_owner'])):
            rstore = await store.dump() # keep store as fresh as possible
            del rstore['quotes'][qindex - 1]
            await store.write(rstore)
            await self.bot.say('The quote specified has been successfully deleted!')
        else:
            await self.bot.say('The quote specified could not be deleted because you do not own it, and are not the bot owner. Sorry!')
