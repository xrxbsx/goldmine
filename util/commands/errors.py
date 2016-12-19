from discord.ext.commands.errors import *

del CommandOnCooldown
class CommandOnCooldown(CommandError):
    """Exception raised when the command being invoked is on cooldown.
    Attributes
    -----------
    cooldown: Cooldown
        A class with attributes ``rate``, ``per``, and ``type`` similar to
        the :func:`cooldown` decorator.
    retry_after: float
        The amount of seconds to wait before you can retry again.
    """
    def __init__(self, cooldown, retry_after, ctx):
        self.cooldown = cooldown
        self.retry_after = retry_after
        self.ctx = ctx
        super().__init__('You are on cooldown. Try again in {:.2f}s'.format(retry_after))

class ReturnError(CommandError):
    """Raised with a message to send it to chat."""
    def __init__(self, msg, ctx):
        self.text = msg.format(ctx)
        self.ctx = ctx
        super().__init__(msg.format(ctx))

class PassException(CommandError):
    """Just pass. Used to simulate the return statement."""
    def __init__(self):
        super().__init__('Pass exception occured. You shouldn\'t be seeing this!')
