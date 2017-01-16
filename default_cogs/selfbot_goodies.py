"""Nice selfbot goodies."""
import asyncio
from datetime import datetime
import util.commands as commands
from util.perms import echeck_perms
from .cog import Cog

class SelfbotGoodies(Cog):
    """Some nice things for selfbot goodies."""

    def __init__(self, bot):
        self.start_time = datetime.now()
        super().__init__(bot)

    @commands.command(pass_context=True)
    async def screenshot(self, ctx):
        await echeck_perms(ctx, ['bot_owner'])
        await self.bot.upload(fp='ugh')

    @commands.command(pass_context=True)
    async def msg_rate(self, ctx):
        await echeck_perms(ctx, ['bot_owner'])
        msg = await self.bot.say('Please wait...')
        start_time = datetime.now()
        m = {'messages': 0}
        async def msg_task(m):
            while True:
                await self.bot.wait_for_message()
                m['messages'] += 1
        task = self.loop.create_task(msg_task(m))
        await asyncio.sleep(8)
        task.cancel()
        time_elapsed = datetime.now() - start_time
        time_elapsed = time_elapsed.total_seconds()
        await self.bot.edit_message(msg, 'I seem to be getting ' + str(round(m['messages'] / time_elapsed, 2)) + ' messages per second.')

def setup(bot):
    bot.add_cog(SelfbotGoodies(bot))

