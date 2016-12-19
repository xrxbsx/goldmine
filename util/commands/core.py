import asyncio
import inspect
from discord.ext.commands.core import *
from .errors import *

def quoted_word(view):
    current = view.current

    if current is None:
        return None

    result = [current]

    while not view.eof:
        current = view.get()
        if not current:
            return ''.join(result)

        if current == '\\':
            next_char = view.get()
            if not next_char:
                # if we aren't then we just let it through
                return ''.join(result)

            # different escape character, ignore it
            view.undo()
            result.append(current)
            continue

        if current.isspace():
            # end of word found
            return ''.join(result)

        result.append(current)

class ProCommand(Command):
    """A class that implements the protocol for a bot text command.
    These are not created manually, instead they are created via the
    decorator or functional interface.
    Attributes
    -----------
    name : str
        The name of the command.
    callback : coroutine
        The coroutine that is executed when the command is called.
    help : str
        The long help text for the command.
    brief : str
        The short help text for the command. If this is not specified
        then the first line of the long help text is used instead.
    aliases : list
        The list of aliases the command can be invoked under.
    pass_context : bool
        A boolean that indicates that the current :class:`Context` should
        be passed as the **first parameter**. Defaults to `False`.
    enabled : bool
        A boolean that indicates if the command is currently enabled.
        If the command is invoked while it is disabled, then
        :exc:`DisabledCommand` is raised to the :func:`on_command_error`
        event. Defaults to ``True``.
    parent : Optional[command]
        The parent command that this command belongs to. ``None`` is there
        isn't one.
    checks
        A list of predicates that verifies if the command could be executed
        with the given :class:`Context` as the sole parameter. If an exception
        is necessary to be thrown to signal failure, then one derived from
        :exc:`CommandError` should be used. Note that if the checks fail then
        :exc:`CheckFailure` exception is raised to the :func:`on_command_error`
        event.
    description : str
        The message prefixed into the default help command.
    hidden : bool
        If ``True``\, the default help command does not show this in the
        help output.
    no_pm : bool
        If ``True``\, then the command is not allowed to be executed in
        private messages. Defaults to ``False``. Note that if it is executed
        in private messages, then :func:`on_command_error` and local error handlers
        are called with the :exc:`NoPrivateMessage` error.
    rest_is_raw : bool
        If ``False`` and a keyword-only argument is provided then the keyword
        only argument is stripped and handled as if it was a regular argument
        that handles :exc:`MissingRequiredArgument` and default values in a
        regular matter rather than passing the rest completely raw. If ``True``
        then the keyword-only argument will pass in the rest of the arguments
        in a completely raw matter. Defaults to ``False``.
    ignore_extra : bool
        If ``True``\, ignores extraneous strings passed to a command if all its
        requirements are met (e.g. ``?foo a b c`` when only expecting ``a``
        and ``b``). Otherwise :func:`on_command_error` and local error handlers
        are called with :exc:`TooManyArguments`. Defaults to ``True``.
    """
    def __init__(self, name, callback, **kwargs):
        super().__init__(name, callback, **kwargs)

    async def prepare(self, ctx):
        ctx.command = self
        self._verify_checks(ctx)
        await self._parse_arguments(ctx)

        if self._buckets.valid:
            bucket = self._buckets.get_bucket(ctx)
            retry_after = bucket.is_rate_limited()
            if retry_after:
                raise CommandOnCooldown(bucket, retry_after, ctx)

    async def transform(self, ctx, param):
        required = param.default is param.empty
        converter = self._get_converter(param)
        consume_rest_is_special = param.kind == param.KEYWORD_ONLY and not self.rest_is_raw
        view = ctx.view
        view.skip_ws()

        if view.eof:
            if param.kind == param.VAR_POSITIONAL:
                raise RuntimeError() # break the loop
            if required:
                raise MissingRequiredArgument('{0.name} is a required argument that is missing.'.format(param))
            return param.default

        if consume_rest_is_special:
            argument = view.read_rest().strip()
        else:
            argument = quoted_word(view)

        try:
            return await self.do_conversion(ctx, converter, argument)
        except CommandError as e:
            raise e
        except Exception as e:
            raise BadArgument('Converting to "{0.__name__}" failed.'.format(converter)) from e


def command(name=None, cls=None, **attrs):
    """A decorator that transforms a function into a :class:`Command`
    or if called with :func:`group`, :class:`Group`.
    By default the ``help`` attribute is received automatically from the
    docstring of the function and is cleaned up with the use of
    ``inspect.cleandoc``. If the docstring is ``bytes``, then it is decoded
    into ``str`` using utf-8 encoding.
    All checks added using the :func:`check` & co. decorators are added into
    the function. There is no way to supply your own checks through this
    decorator.
    Parameters
    -----------
    name : str
        The name to create the command with. By default this uses the
        function name unchanged.
    cls
        The class to construct with. By default this is :class:`Command`.
        You usually do not change this.
    attrs
        Keyword arguments to pass into the construction of the class denoted
        by ``cls``.
    Raises
    -------
    TypeError
        If the function is not a coroutine or is already a command.
    """
    if cls is None:
        cls = ProCommand

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')

        try:
            checks = func.__commands_checks__
            checks.reverse()
            del func.__commands_checks__
        except AttributeError:
            checks = []

        try:
            cooldown = func.__commands_cooldown__
            del func.__commands_cooldown__
        except AttributeError:
            cooldown = None

        help_doc = attrs.get('help')
        if help_doc is not None:
            help_doc = inspect.cleandoc(help_doc)
        else:
            help_doc = inspect.getdoc(func)
            if isinstance(help_doc, bytes):
                help_doc = help_doc.decode('utf-8')

        attrs['help'] = help_doc
        fname = name or func.__name__
        return cls(name=fname, callback=func, checks=checks, cooldown=cooldown, **attrs)

    return decorator
