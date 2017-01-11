"""The quote system!"""
import time
import random
import discord
import util.quote as quote
import util.commands as commands
from util.perms import check_perms
from .cog import Cog

class Quotes(Cog):
    """Quotes from all over the place.
    Enjoy them, and give us some more :3"""

    @commands.command(aliases=['randquote', 'getquote'])
    async def quote(self, *args):
        """Reference a quote.
        Usage: quote {quote number}"""
        try:
            qindx = args[0]
        except IndexError:
            qindx = random.randint(1, self.dstore['quotes'].__len__())
        try:
            qindex = int(qindx)
        except ValueError:
            await self.bot.reply('that isn\'t a number!')
            return
        if qindex < 0:
            await self.bot.reply('there aren\'t negative quotes!')
            return
        try:
            await self.bot.say(quote.qrender(self.dstore['quotes'][qindex - 1], qindex - 1, self.bot))
        except IndexError:
            await self.bot.reply('that quote doesn\'t exist!')

    @commands.command(aliases=['quotes', 'listquote', 'quoteslist', 'listquotes', 'dumpquotes', 'quotedump', 'quotesdump'])
    async def quotelist(self, *rshow_pages: int):
        """List all the quotes.
        Usage: quotelist"""
        # maybe PM this
        show_pages = [i for i in rshow_pages]
        pager = commands.Paginator(prefix='', suffix='', max_size=1595)
        if not show_pages:
            show_pages.append(1)
        for n, i in enumerate(self.dstore['quotes']):
            qout = quote.qrender(i, n, self.bot)
            pager.add_line(qout)
        for page_n in show_pages:
            try:
                await self.bot.say('**__Listing page *{0}* of *{1}* of quotes.__**\n'.format(page_n, len(pager.pages)) + pager.pages[page_n - 1])
            except IndexError:
                await self.bot.say('**__Error: page *{0}* doesn\'t exist! There are *{1}* pages.__**'.format(page_n, len(pager.pages)))

    @commands.command(pass_context=True, aliases=['newquote', 'quotenew', 'addquote', 'makequote', 'quotemake', 'createquote', 'quotecreate', 'aq'])
    async def quoteadd(self, ctx, target: discord.Member, *, text: str):
        """Add a quote.
        Usage: quoteadd [member] [text here]"""
        fmt_time = [int(i) for i in time.strftime("%m/%d/%Y").split('/')]
        bname = await self.store.get_prop(ctx.message, 'bot_name')
        q_template = {
            'id': 0,
            'quote': 'The bot has encountered an internal error.',
            'author': bname,
            'author_ids': [self.bot.user.id],
            'date': fmt_time
        }
        mauthor = target
        q_template['quote'] = text.replace('\n', ' ')
        q_template['author'] = mauthor.display_name
        if mauthor.display_name != mauthor.name:
            q_template['author'] += ' (' + mauthor.name + ')'
        q_template['author_ids'] = [mauthor.id]
        q_template['id'] = len(self.dstore['quotes']) # +1 for next id, but len() counts from 1
        self.dstore['quotes'].append(q_template)
        await self.bot.reply(f'you added quote **#{q_template["id"]}**!')

    @commands.command(pass_context=True, aliases=['quoteedit', 'modquote', 'editquote'])
    async def quotemod(self, ctx, qindex: int, *, text: str):
        """Edit an existing quote.
        Usage: quotemod [quote number] [new text here]"""
        if qindex < 0:
            await self.bot.reply('there aren\'t negative quotes!')
            return
        try:
            q_template = self.dstore['quotes'][qindex - 1]
        except IndexError:
            await self.bot.reply('that quote doesn\'t already exist!')
            return
        mauthor = ctx.message.author
        q_template['quote'] = text.replace('\n', ' ')
        if mauthor.id not in q_template['author_ids']:
            q_template['author'] += ', ' + mauthor.display_name
            if mauthor.display_name != mauthor.name:
                q_template['author'] += ' (' + mauthor.name + ')'
        q_template['author_ids'].extend([mauthor.id])
        q_template['date'] = [int(i) for i in time.strftime("%m/%d/%Y").split('/')]
        self.dstore['quotes'][qindex - 1] = q_template
        await self.bot.reply(f'you edited quote **#{qindex}**!')

    @commands.command(pass_context=True, aliases=['rmquote', 'quoterm', 'delquote'])
    async def quotedel(self, ctx, qindex: int):
        """Delete an existing quote.
        Usage: quotedel [quote number]"""
        if qindex < 0:
            await self.bot.reply('there aren\'t negative quotes!')
            return
        try:
            q_target = self.dstore['quotes'][qindex - 1]
        except IndexError:
            await self.bot.reply(f'quote **#{qindex}** doesn\'t already exist!')
            return
        mauthor = ctx.message.author
        _pcheck = await check_perms(ctx, ['bot_owner'])
        if (mauthor.id == q_target['author_ids'][0]) or (_pcheck):
            del self.dstore['quotes'][qindex - 1]
            await self.bot.reply(f'you deleted quote **#{qindex}**!')
        else:
            await self.bot.reply(f'you can\'t delete quote **#{qindex}** because you didn\'t write it. Sorry!')

def setup(bot):
    c = Quotes(bot)
    bot.add_cog(c)
