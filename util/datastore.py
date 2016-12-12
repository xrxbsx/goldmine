"""Functions for handling the Data Store."""
import asyncio
import os
import json
from util.commands import CommandInvokeError
from util.const import orig_store
from properties import storage_backend

def initialize():
    """Initialize the data store, if needed."""
#    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'storage.json'), 'w+') as storefile:
#        try:
#            json.loads('' + storefile.read())
#        except json.decoder.JSONDecodeError:
#            storefile.write(json.dumps(orig_store, separators=(',', ':')))
    pass

class DataStore():
    """The data store central."""
    exts = {
        'json': 'json',
        'leveldb': 'ldb',
        'pickle': 'db'
    }
    def __init__(self, backend, path=None, join_path=True, commit_interval=3):
        self.dir = os.path.dirname(os.path.realpath(__file__))
        self.backend = backend
        self.session = None
        self.commit_interval = commit_interval
        self.path = ''
        if path:
            if join_path:
                self.path = os.path.join(self.dir, path)
            else:
                self.path = path
        else:
            self.path = os.path.join(self.dir, '..', 'storage.' + self.exts[storage_backend])
        self.store = {}
        if self.backend == 'json':
            with open(self.path, 'r') as storefile:
                self.store = json.loads('' + storefile.read())

    async def read(self):
        """Re-read the datastore from disk, discarding changes."""
        if self.backend == 'json':
            with open(self.path, 'r') as storefile:
                self.store = json.loads('' + storefile.read())

    async def commit(self):
        """Commit the current datastore to disk."""
        with open(self.path, 'w') as storefile:
            storefile.write(json.dumps(self.store, separators=(',', ':')))

    async def commit_task(self):
        while True:
            await asyncio.sleep(self.commit_interval * 60)
            await self.commit()

    async def get_cmdfix(self, msg):
        """Easy method to retrieve the command prefix in current scope."""
        return await self.get_prop(msg, 'command_prefix')

    async def get_props_s(self, msg):
        """Get the server properties of a message."""
        try:
            return self.store['properties']['by_server'][msg.server.id]
        except (KeyError, AttributeError):
            self.store['properties']['by_server'][msg.server.id] = {}
            return {}

    async def get_props_u(self, msg):
        """Get the user properties of a message."""
        try:
            try:
                return self.store['properties']['by_user'][msg.author.id]
            except KeyError:
                self.store['properties']['by_user'][msg.author.id] = {}
                return {}
        except AttributeError: # for Member
            try:
                return self.store['properties']['by_user'][msg.id]
            except KeyError:
                self.store['properties']['by_user'][msg.id] = {}
                return {}

    async def get_props_c(self, msg):
        """Get the channel properties of a message."""
        try:
            return self.store['properties']['by_channel'][msg.server.id +':'+ msg.channel.id]
        except (KeyError, AttributeError):
            self.store['properties']['by_channel'][msg.server.id +':'+ msg.channel.id] = {}
            return {}

    async def set_prop(self, msg, scope: str, prop: str, content):
        try:
            t_scope = self.store['properties'][scope]
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
            self.store['properties'][scope] = t_scope

    async def get_prop(self, msg, prop: str):
        """Get the final property referenced in msg's scope."""
        try: # User
            thing = await self.get_props_u(msg)
            return thing[prop]
        except (KeyError, AttributeError):
            try: # Channel
                thing = await self.get_props_c(msg)
                return thing[prop]
            except (KeyError, AttributeError):
                try: # Server
                    thing = await self.get_props_s(msg)
                    return thing[prop]
                except (KeyError, AttributeError):
                    try:
                        return self.store['properties']['global'][prop]
                    except (KeyError, AttributeError):
                        if prop.startswith('profile_'):
                            return self.store['properties']['global']['profile']
                        else:
                            raise KeyError(str)
