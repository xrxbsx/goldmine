"""Permission handling code."""
from properties import bot_owner
import util.datastore as store
from discord.ext.commands import CommandError

class CommandPermissionError(CommandError):
    """Subclass of CommandError for permission handling errors."""
    pass

async def check_perms(ctx, perms_required):
    """Check permissions required for an action."""
    perms_satisfied = 0
    sender = ctx.message.author
    sender_name = str(sender)
    rstore = await store.dump()
    try:
        sowner = ctx.message.server.owner
        sowner_name = str(sowner)
    except AttributeError: # if in a DM (PrivateChannel)
        sowner = ctx.message.channel.owner
        try:
            sowner_name = str(sowner)
        except AttributeError: # if in a non-group DM (PrivateChannel)
            sowner = sender
            sowner_name = sender_name
    for i in perms_required:
        if i == 'bot_owner':
            if sender_name == bot_owner:
                perms_satisfied += 1
        if i == 'server_owner':
            if sender_name == sowner_name:
                perms_satisfied += 1
        if i == 'bot_admin':
            if (sender_name in rstore['bot_admins']) or (sender_name == bot_owner):
                perms_satisfied += 1
    return bool(perms_required.__len__() == perms_satisfied)

async def echeck_perms(ctx, perms_required):
    """Easy wrapper for permission checking."""
    if not check_perms(ctx, perms_required):
        raise CommandPermissionError(message=ctx.message)
