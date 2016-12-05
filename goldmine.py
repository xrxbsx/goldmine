#!/usr/bin/env python3
"""The launcher for Dragon5232's Discord bot.'"""
from __future__ import print_function
print('The bot is now loading, please wait...')
import sys
print('Running on Python ' + '.'.join([str(i) for i in sys.version_info]))
if sys.version_info[0] < 3: # [3].3
    print('You must be using Python 3.3+! Please upgrade and try again.')
    exit(1)
if sys.version_info[1] < 3: # 3.[3]
    print('You must be using Python 3.3+! Please upgrade and try again.')
    exit(1)
if sys.version_info[1] < 5:
    print('You\'re using Python 3.3 or 3.4. This will require the old syntax converter.')
    print('Press Enter to convert. Note: not ALL features will work.')
    input()
    print('Not implemented yet. Run convert_to_old_syntax.py manually.')
    exit(0)
if sys.version_info[1] == 3:
    print('You\'re using Python 3.3. This will require the discord.py requirements hack as well.')
    print('Press Enter to install the fixed library. Note: not ALL features will work.')
    input()
    print('Not implemented yet. Manually install discord.py with aiohttp==0.17.4.')
    exit(0)
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
