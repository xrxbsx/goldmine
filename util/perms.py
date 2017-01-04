"""Permission handling code."""
import asyncio
from properties import bot_owner
from util.commands.errors import CommandPermissionError, OrCommandPermissionError

async def check_perms(ctx, perms_required):
    """Check permissions required for an action."""
    perms_satisfied = 0
    sender = ctx.message.author
    sender_id = sender.id
    dc_perms = [k[0] for k in list(ctx.message.author.permissions_in(ctx.message.channel)) if k[1]]
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
        elif (i == 'server_owner') and (sender_id == sowner_id):
            perms_satisfied += 1
        elif (i == 'bot_admin') and ((sender_id in ctx.bot.store.store['bot_admins']) or (sender_id == bot_owner)):
            perms_satisfied += 1
        elif i.lower() in dc_perms:
            perms_satisfied += 1
    if sender_id == bot_owner:
        return True
    return len(perms_required) == perms_satisfied

async def echeck_perms(ctx, perms_required):
    """Easy wrapper for permission checking."""
    tmp = await check_perms(ctx, perms_required)
    if not tmp:
        raise CommandPermissionError(perms_required, message=ctx.message.content)

async def or_check_perms(ctx, perms_ok):
    """Easy wrapper for permission checking."""
    results = set()
    for perm in perms_ok:
        res = await check_perms(ctx, [perm])
        results.add(res)
    if True not in results:
        raise OrCommandPermissionError(perms_ok, message=ctx.message.content)
