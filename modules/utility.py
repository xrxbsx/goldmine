"""Definition of the bot's Utility module.'"""
import discord
from discord.ext import commands
from .cog import Cog


class Utility(Cog):
    """Random commands that can be useful here and there.
    Settings, properties, and other stuff can be found here.
    """

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
        await self.bot.say(' '.join(args))