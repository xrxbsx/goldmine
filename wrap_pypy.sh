#!/bin/bash

#cd "$(dirname \"$0\")"
PYPY_PATH="~/pypy33/bin/pypy3"
while true
do
    sleep 5
    echo "Launching bot"
    $PYPY_PATH goldmine.py
    echo "Clearing changes since last commit"
    git reset HEAD --hard
    echo "Updating code"
    git pull -v
    echo "Translating to Python 3.3.x asyncio syntax"
    $PYPY_PATH convert-to-old-syntax.py
done
