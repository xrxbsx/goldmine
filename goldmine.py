"""The launcher for Dragon5232's Discord bot.'"""
from __future__ import print_function
print('The bot is now loading, please wait...')
import sys
import asyncio
while True:
    print(' - Loading bot code')
    import core
    print(' - Ready to start bot!')
    retval = core.main()
    print(' - Bot stopped.')
    if retval: # restart
        print(' - Restarting bot.')
        exit(0)
        print(' - Unloading old code')
        del core
        del sys.modules['core']
        print(' - Discarding old event loop')
        loop_old = asyncio.get_event_loop()
        loop_old.close()
        print(' - Creating new event loop')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print(' - Ready to start bot!')
    else:
        print(' - Exiting.')
        exit(0)
