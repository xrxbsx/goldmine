#!/bin/bash

#cd "$(dirname \"$0\")"
PYPY_PATH="~/pypy33/bin/pypy3"
export PATH="$PYPY_PATH:$PATH"
while true
do
    sleep 5
    echo "Launching bot"
    pypy3 goldmine.py
    echo "Clearing changes since last commit"
    git reset HEAD --hard
    echo "Updating code"
    git pull -v
    echo "Translating to Python 3.3.x asyncio syntax"
    pypy3 convert-to-old-syntax.py
done
