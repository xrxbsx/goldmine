#!/bin/bash

cd "$(dirname \"$0\")"
while true
do
    echo "Launching bot"
    $PYPY_PATH goldmine.py
    echo "Clearing changes since last commit"
    git reset HEAD --hard
    echo "Updating code"
    git pull -v
    echo "Translating to Python 3.3.x asyncio syntax"
    $PYPY_PATH convert-to-old-syntax.py
done
