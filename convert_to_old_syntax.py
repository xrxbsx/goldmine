#!/usr/bin/env python3

from __future__ import print_function
from fnmatch import filter
import os
import re

cur_dir = os.path.dirname(os.path.abspath(__file__))

def rc_files(folder):
    rl = set()
    for root, fds, files in os.walk(folder):
        for fn in files:
            rl.add(os.path.join(root, fn))
    return rl

def main():
    targets = filter(rc_files(cur_dir), '*.py')
    for target in targets:
        with open(target, 'r+') as f:
            contents = f.read()
            f.seek(0)
            f.truncate(0)
            final = re.sub('await ', 'yield from ', contents)
#            final = re.sub(r'(^\s*async def )', r'@asyncio.coroutine\n\1', final)
            final = re.sub('async def ', '@asyncio.coroutine\ndef ', final)
            final = re.sub('    @asyncio.coroutine\ndef ', '    @asyncio.coroutine\n    def ', final)
            final = re.sub('async with ', 'with ', final)
            final = re.sub('async for ', 'for ', final)
#            print(final)
#            input()
            f.write(final)

if __name__ == '__main__':
    main()
