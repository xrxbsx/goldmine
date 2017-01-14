"""Awesome auto cucumber."""
from collections import Counter
from util.autocorrect import Corrector
from util.perms import echeck_perms
import util.dynaimport as di
from .cog import Cog

for mod in ['os', 're', 'copy', 'aiohttp',
            'async_timeout']:
    globals()[mod] = di.load(mod)
commands = di.load('util.commands')

class AutoCucumber(Cog):
    """Spelling corrector :)"""
    special_chars = list('~`!@#$%^&*()-_=+[{]}\\|:;<,>.?/\'"')
    punctuation_chars = list(';!?.,:')
    def __init__(self, bot):
        super().__init__(bot)
        self.enabled = False
        self.corrections = {}
        self.corrector = None
        self.loop.create_task(self.create_corrector())
        self.load_data()

    def load_data(self, text=None):
        """Load and parse spelling data."""
        if text is None:
            with open(os.path.join(self.bot.dir, 'assets', 'corrections.txt')) as f:
                text = f.read()
        items = text.split('\n')
        raw_pairs = [item.split('->') for item in items]
        for pair in raw_pairs:
            self.corrections[pair[0]] = pair[1].split(', ')[0]

    async def init_corrector(self):
        with async_timeout.timeout(16):
            async with aiohttp.request('GET', 'http://norvig.com/big.txt') as r:
                text = await r.text()
        with open(os.path.join(self.bot.dir, 'data', 'autocorrect.txt'), 'a') as f:
            f.write(text)
        self.corrector = await self.loop.run_in_executor(None, lambda: Corrector())

    async def create_corrector(self):
        """Create the auto correction engine."""
        try:
            self.corrector = await self.loop.run_in_executor(None, lambda: Corrector())
        except FileNotFoundError:
            await self.init_corrector()

    async def on_not_command(self, msg):
        if self.enabled:
            old = copy.copy(msg)
            words = re.findall(r"[\w']+|[.,!?;:]", msg.content)
            emoji_re = re.compile(u'[\U00010000-\U0010ffff\u2615]')
            #words = [w.lower() for w in words]
            result = ''
            for word in words:
                if '`' in word:
                    result += word
                elif word in self.punctuation_chars:
                    result = result[:-1]
                    result += word + ' '
                elif word in self.special_chars:
                    result += word
                elif re.findall(emoji_re, word):
                    result += word + ' '
                elif word in self.corrections:
                    result += self.corrections[word] + ' '
                else:
                    result += self.corrector.correct(word) + ' '
            #final = result[0].upper() + result[1:]
            final = result
            raw_final = final.replace('\u200b', '').replace('\n', '')
            raw_msg_content = msg.content.replace('\u200b', '').replace('\n', '')
            if raw_final != raw_msg_content:
                await self.bot.edit_message(msg, final)

    @commands.command(pass_context=True)
    async def tac(self, ctx):
        await echeck_perms(ctx, ['bot_owner'])
        self.enabled = not self.enabled
        await self.bot.say('Autocucumber is now ' + ('on.' if self.enabled else 'off.'))

def setup(bot):
    bot.add_cog(AutoCucumber(bot))

