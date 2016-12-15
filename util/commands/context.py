from discord.ext.commands.context import Context as ExtContext
from ..func import bdel

class ProContext(ExtContext):
    def __init__(self, **attrs):
        super().__init__(**attrs)
        self.raw_args = bdel(self.message.content, self.prefix + self.invoked_with + ' ')
