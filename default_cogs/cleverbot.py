"""Good ol' Cleverbot."""
import asyncio
import random
from util.cleverbot import Cleverbot as RealCleverbot
import util.commands as commands
from .cog import Cog

class Cleverbot(Cog):
    """Good ol' Cleverbot."""

    def __init__(self, bot):
        self.cb = RealCleverbot(get_cookies=False)
        self.cleverbutt_timers = set()
        self.cleverbutt_latest = {}
        self.cleverbutt_replied_to = set()
        super().__init__(bot)

    async def on_ready(self):
        try:
            await self.cb.get_cookies()
        except asyncio.TimeoutError:
            self.logger.warning('Couldn\'t get cookies for Cleverbot, so it probably won\'t work.')

    async def askcb(self, query):
        """A method of querying Cleverbot safe for async."""
        return await self.cb.ask(query)

    async def auto_cb_convo(self, msg, kickstart, replace=False):
        """Cleverbot auto conversation manager."""
        if self.status == 'invisible': return
        await self.bot.send_typing(msg.channel)
        lmsg = msg.content.lower().replace('@everyone', 'everyone').replace('@here', 'here')
        if replace:
            cb_string = lmsg.replace(kickstart, '')
        else:
            cb_string = bdel(lmsg, kickstart)
        reply_bot = await self.askcb(cb_string)
        await self.bot.msend(msg, msg.author.mention + ' ' + reply_bot)

    async def clever_reply(self, msg):
        self.cleverbutt_timers.add(msg.server.id)
        await asyncio.sleep((random.random()) * 2)
        await self.bot.send_typing(msg.channel)
        try:
            query = self.cleverbutt_latest[msg.server.id]
        except KeyError:
            query = msg.content
        reply_bot = await self.askcb(query)
        s_duration = (((len(reply_bot) / 15) * 1.4) + random.random()) - 0.2
        await asyncio.sleep(s_duration / 2)
        await self.bot.send_typing(msg.channel)
        await asyncio.sleep((s_duration / 2) - 0.4)
        await self.bot.msend(msg, reply_bot)
        await asyncio.sleep(1)
        try:
            del self.cleverbutt_latest[msg.server.id]
        except Exception:
            pass
        self.cleverbutt_replied_to.add(msg.id)
        self.cleverbutt_timers.remove(msg.server.id)

    @commands.command(aliases=['cb', 'ask', 'ai', 'bot'])
    async def cleverbot(self, *, query: str):
        """Queries the Cleverbot service. Because why not.
        Usage: cleverbot [message here]"""
        try:
            reply_bot = await self.askcb(query)
        except IndexError:
            reply_bot = '**Couldn\'t get a response from Cleverbot!**'
        await self.bot.say(reply_bot)

def setup(bot):
    """Set up the cog."""
    bot.add_cog(Cleverbot(bot))
