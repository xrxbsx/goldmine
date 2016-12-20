"""General utility functions."""
import contextlib
from asyncio import ensure_future
from functools import partial
import datetime
def bdel(s, r): return (s[len(r):] if s.startswith(r) else s)

class DiscordFuncs():
    def __init__(self, bot):
        self.bot = bot
    def __getattr__(self, name):
        new_func = None
        coro = getattr(self.bot, name)
        if not callable(coro):
            raise AttributeError('Class can only access client functions')
        def async_wrap(coro, *args, **kwargs):
            ensure_future(coro(*args, **kwargs))
        new_func = partial(async_wrap, coro)
        new_func.__name__ = coro.__name__
        new_func.__qualname__ = coro.__qualname__
        return new_func

def _import(mod_name, var_name=None, attr_name=''):
    ret = "globals()['{}'] = imp('{}')"
    if var_name:
        if attr_name:
            attr_name = '.' + attr_name
        ret = ret.format(var_name, mod_name) + attr_name
    else:
        ret = ret.format(mod_name, mod_name)
    return ret


def _set_var(var_name, expr):
    return "globals()['{}'] = {}".format(var_name, expr)

def _del_var(var_name):
    return "del globals()['{}']".format(var_name)

snowtime = lambda i: datetime.datetime.fromtimestamp(((float(int(i)) / 4194304.0) + 1420070400000.0 + 18000000.0) / 1000.0).strftime('%a %b %d, %Y %I:%M:%S %p')

class PrintException(Exception):
    """An exception that prints the error."""
    def __init__(self, err):
        print(str(err))
        self.err = err
        super().__init__()

@contextlib.contextmanager
def assert_msg(ctx, msg: str):
    """Assert. If error, send msg."""
    try:
        yield
    except AssertionError:
        ctx.bot.send_message(ctx.message.channel, msg)
        raise PassException()
