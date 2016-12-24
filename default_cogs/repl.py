"""The REPL module for power users."""
import traceback
import discord
import inspect
from contextlib import redirect_stdout
import io
import util.commands as commands
from util.perms import echeck_perms
from .cog import Cog

class REPL(Cog):
    def __init__(self, bot):
        self.sessions = set()
        super().__init__(bot)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(e, '^', type(e).__name__)

    @commands.command(pass_context=True, hidden=True)
    async def repl(self, ctx, *alt_prefix: str):
        await echeck_perms(ctx, ['bot_owner'])
        msg = ctx.message

        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': msg,
            'server': msg.server,
            'channel': msg.channel,
            'author': msg.author,
            'last': None,
            'kek': 'lol',
            'self': self,
            'msg': msg,
            'test': 'Test right back at ya!'
        }

        if msg.channel.id in self.sessions:
            await self.bot.say('Already running a REPL session in this channel. Exit it with `quit`.')
            return
        self.sessions.add(msg.channel.id)

        if alt_prefix:
            prefix = ' '.join(alt_prefix)
        else:
            prefix = '`'

        await self.bot.say(f'Enter code to execute or evaluate. `exit()` or `quit` to exit. Prefix is: ```{prefix}```')
        while True:
            response = await self.bot.wait_for_message(author=msg.author, channel=msg.channel, check=lambda m: m.content.startswith(prefix))

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await self.bot.say('Exiting.')
                self.sessions.remove(msg.channel.id)
                return

            executor = exec
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as e:
                    await self.bot.say(self.get_syntax_error(e))
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception as e:
                value = stdout.getvalue()
                fmt = '{}{}\n'.format(value, traceback.format_exc())
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = f'{value}{result}\n'
                    variables['last'] = result
                elif value:
                    fmt = f'{value}\n'

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        for i in range(0, len(fmt), 1990):
                           await self.bot.send_message(msg.channel, '```py\n%s```' % fmt[i:i+1990])
                    else:
                        await self.bot.send_message(msg.channel, f'```py\n{fmt}```')
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await self.bot.send_message(msg.channel, f'Unexpected error: `{e}`')

def setup(bot):
    bot.add_cog(REPL(bot))
