"""Server stats reporting."""
import json
import aiohttp
import async_timeout
import util.commands as commands
from .cog import Cog

try:
    from ex_props import discord_bots_token
except ImportError:
    discord_bots_token = None

class DiscordBots(Cog):
    """Reporter of server stats to services like Discord Bots."""

    def __init__(self, bot):
        self.http = None
        super().__init__(bot)
        self.loop.create_task(self.init_http())

    def __unload(self):
        self.http.close()

    async def init_http(self):
        self.http = aiohttp.ClientSession()

    async def update(self):
        """Report the current server count to bots.discord.pw."""
        if not discord_bots_token:
            self.logger.warning('Tried to contact Discord Bots, but no token set!')
            return False
        data = dict(server_count=len(self.bot.servers))
        dest = 'https://bots.discord.pw/api/bots/' + self.bot.user.id + '/stats'
        headers = {
            'Authorization': discord_bots_token,
            'Content-Type': 'application/json'
        }
        with async_timeout.timeout(6):
            async with self.http.post(dest, data=json.dumps(data), headers=headers) as r:
                resp_key = f'(got {r.status} {r.reason})'
                if r.status == 200:
                    self.logger.info('Successfully sent Discord Bots our guild count ' + resp_key)
                else:
                    self.logger.warning('Failed sending our guild count to Discord Bots! ' + resp_key)

    async def on_ready(self):
        await self.update()
    async def on_server_join(self, server):
        await self.update()
    async def on_server_remove(self, server):
        await self.update()

def setup(bot):
    if bot.selfbot:
        bot.logger.warning('Tried to load cog Discord Bots, but we\'re a selfbot. Not loading.')
    else:
        bot.add_cog(DiscordBots(bot))
