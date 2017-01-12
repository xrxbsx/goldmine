"""Nice selfbot goodies."""
from datetime import datetime
import util.commands as commands
from util.perms import echeck_perms
from .cog import Cog

class SelfbotGoodies(Cog):
    """Some nice things for selfbot goodies."""

    def __init__(self, bot):
        self.messages = 0
        self.start_time = datetime.now()
        super().__init__(bot)

    @commands.command(pass_context=True)
    async def screenshot(self, ctx):
        await echeck_perms(ctx, ['bot_owner'])
        await self.bot.upload(fp='ugh')

    async def on_message(self, msg):
        self.messages += 1

    @commands.command(pass_context=True)
    async def msg_rate(self, ctx):
        await echeck_perms(ctx, ['bot_owner'])
        time_elapsed = datetime.now() - self.start_time
        time_elapsed = time_elapsed.total_seconds()
        await self.bot.say('I seem to be getting ' + str(round(self.messages / time_elapsed, 2)) + ' messages per second.')

    @commands.command(pass_context=True)
    async def console_msg(self, ctx):
        await echeck_perms(ctx, ['bot_owner'])
        def console_task(ch):
            while True:
                text_in = input('Message> ')
                if text_in == 'quit':
                    return
                else:
                    self.loop.create_task(self.bot.send_message(ch, text_in))
        await self.bot.say('Now entering: Console message mode')
        print('Type \'quit\' to exit.')
        await self.loop.run_in_executor(None, console_task, ctx.message.channel)
        await self.bot.say('Exited console message mode')

def setup(bot):
    bot.add_cog(SelfbotGoodies(bot))

