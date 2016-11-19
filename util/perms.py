from properties import bot_owner

def check_perms(ctx, perms_required):
    perms_satisfied = 0
    sender = ctx.message.author
    sender_name = sender.name + '#' + str(sender.discriminator)
    try:
        sowner = ctx.message.server.owner
        sowner_name = sowner.name + '#' + str(sowner.discriminator)
    except AttributeError: # if in a DM (PrivateChannel)
        sowner = ctx.message.channel.owner
        try:
            sowner_name = sowner.name + '#' + str(sowner.discriminator)
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
    if perms_required.__len__() == perms_satisfied:
        return True
    else:
        return False
