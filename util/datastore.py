"""Functions for handling the Data Store."""
import asyncio
import os
import json
from discord.ext.commands import CommandInvokeError
from properties import storage_backend
from util.const import orig_store

f_exts = {
    'json': 'json'
}

async def get_dir():
    return os.path.dirname(os.path.realpath(__file__))

async def dump():
    """Dump the entire data store's contents.'"""
    c_dir = await get_dir()
    with open(os.path.join(c_dir, '..', 'storage.' + f_exts[storage_backend]), 'r') as storefile:
        return json.loads('' + storefile.read())

async def write(newstore):
    """Write a new dictionary as the data store."""
    c_dir = await get_dir()
    with open(os.path.join(c_dir, '..', 'storage.' + f_exts[storage_backend]), 'w') as storefile:
        storefile.write(json.dumps(newstore, indent=1, separators=(',', ':')))

async def reset():
    """Reset the data store to the stock values."""
    c_dir = await get_dir()
    with open(os.path.join(c_dir, '..', 'storage.' + f_exts[storage_backend]), 'w') as storefile:
        storefile.write(json.dumps(orig_store, indent=1, separators=(',', ':')))

async def read(*depths):
    """Read a specific entry or entry hierarchy from the data store."""
    pass

def initialize():
    """Initialize the data store, if needed."""
#    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'storage.json'), 'w+') as storefile:
#        try:
#            json.loads('' + storefile.read())
#        except json.decoder.JSONDecodeError:
#            storefile.write(json.dumps(orig_store, indent=1, separators=(',', ':')))
    pass

async def get_props_s(msg):
    """Get the server properties of a message."""
    rs = await dump()
    try:
        return rs['properties']['by_server'][msg.server.id]
    except (KeyError, AttributeError):
        rs['properties']['by_server'][msg.server.id] = {}
        await write(rs)
        return {}

async def get_props_u(msg):
    """Get the user properties of a message."""
    rs = await dump()
    try:
        return rs['properties']['by_user'][msg.author.id]
    except (KeyError, AttributeError):
        rs['properties']['by_user'][msg.author.id] = {}
        await write(rs)
        return {}

async def get_props_c(msg):
    """Get the channel properties of a message."""
    rs = await dump()
    try:
        return rs['properties']['by_channel'][msg.server.id +':'+ msg.channel.id]
    except (KeyError, AttributeError):
        rs['properties']['by_channel'][msg.server.id +':'+ msg.channel.id] = {}
        await write(rs)
        return {}

async def get_prop(msg, prop: str):
    """Get the final property referenced in msg's scope."""
    try: # User
        thing = await get_props_u(msg)
        return thing[prop]
    except (KeyError, AttributeError):
        try: # Channel
            thing = await get_props_c(msg)
            return thing[prop]
        except (KeyError, AttributeError):
            try: # Server
                thing = await get_props_s(msg)
                return thing[prop]
            except (KeyError, AttributeError):
                try:
                    rs = await dump()
                    return rs['properties']['global'][prop]
                except (KeyError, AttributeError):
                    if prop.startswith('profile_'):
                        return rs['properties']['global']['profile']
                    else:
                        raise KeyError(str)

async def get_cmdfix(msg):
    """Easy method to retrieve the command prefix in current scope."""
    tmp = await get_prop(msg, 'command_prefix')
    return tmp

async def set_prop(msg, scope: str, prop: str, content):
    """Set a property... absolutely."""
    rstore = await dump()
    try:
        t_scope = rstore['properties'][scope]
    except (KeyError, AttributeError):
        raise CommandInvokeError(AttributeError('Invalid scope specified. Valid scopes are by_user, by_channel, by_server, and global.'))
    else:
        if scope == 'by_user':
            t_scope[msg.author.id][prop] = content
        elif scope == 'by_channel':
            t_scope[msg.channel.id][prop] = content
        elif scope == 'by_server':
            t_scope[msg.server.id][prop] = content
        elif scope == 'global':
            t_scope[prop] = content
        else:
            raise CommandInvokeError(AttributeError('Invalid scope specified. Valid scopes are by_user, by_channel, by_server, and global.'))
        rstore['properties'][scope] = t_scope
        await write(rstore)
