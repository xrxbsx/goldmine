"""The bot's Cozmo module. Only works with Cozmo!"""
import asyncio
import functools
import cozmo
from cozmo.run import FirstAvailableConnector
import util.commands as commands
from .cog import Cog
conn = cozmo.conn

class Cozmo(Cog):
    """Some commands to interface with Cozmo robots.
    You probably don't want this in the open.
    """

    def __init__(self, bot):
        self.sdk_conn = None
        self.robot = None
        self.default_connector = FirstAvailableConnector()
        super().__init__(bot)

    async def check_conn(self, ctx=None):
        """Check the connection to Cozmo."""
        if not self.robot:
#            raise commands.ReturnError('{0.message.author.mention} **Not connected to Cozmo!**', ctx)
            await self.bot.say('Not connected to Cozmo!')
            raise commands.PassException()

    @commands.command()
    async def cspeak(self, *, text: str):
        """Make Cozmo speak something.
        Usage: cspeak [stuff to say]"""
        await self.check_conn()
        status = await self.bot.say('Talking...')
        c_voice = bool('[VOICE:N]' not in text)
        self.robot.say_text(text.replace('[VOICE:N]', '')[:255], use_cozmo_voice=c_voice, duration_scalar=0.9)

    @commands.command()
    async def cdrive(self, drive_time: float):
        """Make Cozmo drive for n seconds.
        Usage: cdrive [seconds to drive]"""
        await self.check_conn()
        status = await self.bot.say('Driving...')
        await self.robot.drive_wheels(50, 50, 50, 50, duration=drive_time)
        await self.bot.edit_message(status, 'Finished driving!')

    @commands.command(aliases=['cinit'])
    async def cinitialize(self):
        """Connect to Cozmo.
        Usage: cinit"""
        try:
            self.sdk_conn = await self.cozmo_connect(self.loop)
        except cozmo.ConnectionError as e:
            await self.bot.say("A connection error occurred: %s" % e)
            return False
        self.robot = await self.sdk_conn.wait_for_robot()
        await self.bot.say('Connected to robot!')

    async def cozmo_connect(self, loop, conn_factory=conn.CozmoConnection, connector=None):
        '''Uses the supplied event loop to connect to a device.
        Returns:
            A :class:`cozmo.conn.CozmoConnection` instance.
        '''
        if connector is None:
            connector = self.default_connector

        factory = functools.partial(conn_factory, loop=loop)
        async def conn_check(coz_conn):
            await coz_conn.wait_for(conn.EvtConnected, timeout=5)
        async def connect():
            return await connector.connect(loop, factory, conn_check)

        transport, coz_conn = await connect()
        return coz_conn

def setup(bot):
    c = Cozmo(bot)
    bot.add_cog(c)
