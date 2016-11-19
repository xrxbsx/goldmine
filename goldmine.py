"""The launcher for Dragon5232's Discord bot.'"""
from __future__ import print_function
print('The bot is now loading, please wait...')
import sys
while True:
    import core
    retval = core.main()
    if retval:
        del core
        del sys.modules['core']
    else:
        exit(0)
