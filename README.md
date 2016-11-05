# Goldmine
This is Goldmine, a new bot for Discord that keeps things nice and smug.
This bot is written in Python 3, and uses discord.py and asyncio for performance.
###Warning: Work In Progress!

# Features
Commands: 
 - purge [channel] - Removes all messages sent by this bot in the specified channel.

# Installation
Simply run `python3 -m pip install -U discord.py[voice]` to install discord.py with voice support, and `python3 -m pip install -r requirements.txt` to install the rest of the dependencies.
Next, you'll need to create a bot account on Discord and get your bot authentication token. Create a new file called `token.py` in the same folder as `goldmine.py`, and insert the following:
```python
bot_token = 'INSERT_YOUR_TOKEN_HERE'
```
Replace INSERT_YOUR_TOKEN_HERE with your actual token. Make sure you keep the quotes, though!

####Now simply run `python3 goldmine.py` and your bot is good to go!
