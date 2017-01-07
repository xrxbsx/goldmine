"""Definition of the bot's Roleplay module."""
import random
import discord
import util.commands as commands
from util.const import adjs, fights, death
from .cog import Cog

class Roleplay(Cog):
    """Commands related to roleplay.
    Examples: poking, stabbing, and color roles.
    """

    def __init__(self, bot):
        super().__init__(bot)

    @commands.command(pass_context=True, name='rmember', aliases=['randmember', 'randommember', 'randmem', 'rmem', 'draw'], no_pm=True)
    async def rand_member(self, ctx):
        """Choose a random member from the message's server."""
        satisfied = False
        m_list = list(ctx.message.server.members)
        while not satisfied:
            rmem = random.choice(m_list)
            satisfied = str(rmem.status) == 'online'
        await ctx.bot.say(rmem.mention)
        return rmem

    @commands.command(pass_context=True, aliases=['boop', 'poke', 'hit'])
    async def slap(self, ctx, target: str):
        """Slap someone for the win.
        Usage: slap [person]"""
        cmdfix = await self.store.get_cmdfix(ctx.message.content)
        keystr = '* ' + ctx.message.content.split(' ')[0].strip(cmdfix) + 's *'
        await self.bot.say('*' + ctx.message.author.display_name + keystr +
                           target + '* **' + random.choice(adjs) + '**.')

    @commands.command(pass_context=True, aliases=['stab', 'kill', 'punch', 'shoot', 'hurt', 'fight'])
    async def attack(self, ctx, target: str):
        """Hurt someone with determination in the shot.
        Usage: attack [person]"""
        await self.bot.say('*' + ctx.message.author.display_name + '* ' +
                           random.choice(fights).format('*' + target + '*') + '. '
                           + random.choice(death).format('*' + target + '*'))

    @commands.command()
    async def charlie(self, *, question: str):
        """Ask a question... Charlie Charlie are you there?
        Usage: charlie [question to ask, without punctuation]"""
        aq = '' if question.endswith('?') else '?'
        await self.bot.say('*Charlie Charlie* ' + question + aq + "\n**" +
                           random.choice(['Yes', 'No']) + '**')

    @commands.command(pass_context=True)
    async def mentionme(self, ctx):
        """Have the bot mention yourself. Useful for testing.
        Usage: mentionme"""
        await self.bot.say('Hey there, ' + ctx.message.author.mention + '!')

    @commands.command(pass_context=True)
    async def mention(self, ctx, *, target: discord.Member):
        """Make the bot mention someone. Useful for testing.
        Usage: mention [mention, nickname, DiscordTag, or username]"""
        await self.bot.say('Hey there, ' + target.mention + '!')

    @commands.command(pass_context=True, aliases=['gif', 'soontm', 'tm'])
    async def soon(self, ctx):
        """Feel the loading of 10000 years, aka Soon™.
        Usage: soon"""
        with open('assets/soon.gif', 'rb') as image:
            await self.bot.send_file(ctx.message.channel, image, filename='coming_soon.gif')

def setup(bot):
    c = Roleplay(bot)
    bot.add_cog(c)
