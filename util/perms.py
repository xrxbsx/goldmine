"""Permission handling code."""
import asyncio
from properties import bot_owner
from util.commands import CommandError

class CommandPermissionError(CommandError):
    """Subclass of CommandError for permission handling errors."""
    def __init__(self, perms_required, message=None, *args):
        self.perms_required = perms_required
        super().__init__(message=message, *args)

async def check_perms(ctx, perms_required):
    """Check permissions required for an action."""
    perms_satisfied = 0
    sender = ctx.message.author
    sender_id = sender.id
    try:
        sowner = ctx.message.server.owner
        sowner_id = sowner.id
    except AttributeError: # if in a DM (PrivateChannel)
        sowner = ctx.message.channel.owner
        try:
            sowner_id = sowner.id
        except AttributeError: # if in a non-group DM (PrivateChannel)
            sowner = sender
            sowner_id = sender_id
    for i in perms_required:
        if i == 'bot_owner':
            pass
        if i == 'server_owner':
            if sender_id == sowner_id:
                perms_satisfied += 1
        if i == 'bot_admin':
            if (sender_id in ctx.bot.store.store['bot_admins']) or (sender_id == bot_owner):
                perms_satisfied += 1
        if i == 'server_admin':
            if sender.server_permissions.manage_server:
                perms_satisfied += 1
    if sender_id == bot_owner:
        return True
    return bool(perms_required.__len__() == perms_satisfied)

async def echeck_perms(ctx, perms_required):
    """Easy wrapper for permission checking."""
    tmp = await check_perms(ctx, perms_required)
    if not tmp:
        raise CommandPermissionError(perms_required, message=ctx.message.content)
