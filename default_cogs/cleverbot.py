"""Good ol' Cleverbot."""
import asyncio
import random
from util.cleverbot import Cleverbot as RealCleverbot
try:
    from cleverbot import Cleverbot as RealRealCleverbot
except ImportError:
    class RealRealCleverbot:
        """Bogus cleverbot."""
        def ask(self, q):
            return 'The bot owner hasn\'t set up Cleverbot.'
import util.commands as commands
from util.func import bdel
from .cog import Cog

class Cleverbot(Cog):
    """Good ol' Cleverbot."""

    def __init__(self, bot):
        self.cb = RealCleverbot(get_cookies=False) # broken?
        self.real_cb = RealRealCleverbot()
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
        try:
            #return await self.cb.ask(query)
            return await self.loop.run_in_executor(None, self.real_cb.ask, query)
        except IndexError:
            return 'Couldn\'t get a response from Cleverbot.'

    async def auto_cb_convo(self, msg, kickstart, replace=False):
        """Cleverbot auto conversation manager."""
        if self.bot.status == 'invisible': return
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
        await asyncio.sleep(random.random() * 1.8)
        await self.bot.send_typing(msg.channel)
        try:
            query = self.cleverbutt_latest[msg.server.id]
        except KeyError:
            query = msg.content
        reply_bot = await self.askcb(query)
        s_duration = (((len(reply_bot) / 15) * 1.4) + random.random()) - 0.2
        await asyncio.sleep(s_duration / 3)
        await self.bot.send_typing(msg.channel)
        await asyncio.sleep((s_duration / 3) - 0.4)
        await self.bot.msend(msg, reply_bot)
        await asyncio.sleep(0.5)
        try:
            del self.cleverbutt_latest[msg.server.id]
        except Exception:
            pass
        self.cleverbutt_replied_to.add(msg.id)
        self.cleverbutt_timers.remove(msg.server.id)

    async def on_bot_message(self, msg):
        """Cleverbutt message handling magic."""
        if str(msg.channel) == 'cleverbutts':
            if msg.server.id in self.cleverbutt_timers: # still on timer for next response
                self.cleverbutt_latest[msg.server.id] = msg.content
            else:
                await self.clever_reply(msg)

    async def on_mention(self, msg):
        """Cleverbot on-mention logic."""
        if msg.server.id == '110373943822540800': return
        await self.auto_cb_convo(msg, self.bot.user.mention, replace=True)

    async def on_not_command(self, msg):
        """Cleverbutts kickstarting logic."""
        if str(msg.channel) == 'cleverbutts':
            if self.bot.status == 'invisible': return
            if msg.content.lower() == 'kickstart':
                await self.bot.msend(msg, 'Hi, how are you doing?')
                return

    async def on_pm(self, msg):
        """PM replying logic."""
        await self.bot.send_typing(msg.channel)
        cb_reply = await self.askcb(msg.content)
        return await self.bot.msend(msg, ':speech_balloon: ' + cb_reply)

    async def on_prefix_convo(self, msg, lbname):
        """Reply to prefix conversation."""
        return await self.auto_cb_convo(msg, lbname)

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
