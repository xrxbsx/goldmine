# Goldmine
This is Goldmine, a new bot for Discord that keeps things nice and smug.
This bot is written in Python 3, and uses discord.py and asyncio for performance.
###Warning: Work In Progress!

# Features
- Commands:
 - purge [channel] - Removes all messages sent by this bot in the specified channel.
 - Too many more to list.
- Auto-conversation: start a friendly conversation with the bot!
 - Mentions work
 - You can also initiate it like `goldmine heya there, you awake?` and it triggers auto-conversation.
 - Auto-conversations automatically end when the questions stop.
 - Auto-conversations apply per-user and per-channel, which means they won't interfere with other stuff - yay!
 - Dynamic bot names
- DM conversations: have some fun here :)
- Per-server bot name and command prefix :D

# Installation
###Two-Click (Public Instance)
####This method is extremely easy, but may not offer the best performance and/or reliability. Overall, better.
Just click this link: [Click to add GOLDMINE and CO. to your server](https://discordapp.com/api/oauth2/authorize?client_id=239775420470394897&scope=bot&permissions=66321471 "Click to add GOLDMINE to your server!"), select a server, click **Done**, and you're all set! Easy as pie :)

You might want to set the command prefix and/or bot name for your server. To do so, simply make sure you're a server admin (Manage Server permission), and type: 
 - `!setprop bot_name MyAwesomeBot` for bot name, replacing **MyAwesomeBot** with your desired name.
 - `!setprop command_prefix $` for command prefix, replacing **$** with your desired prefix.
###Manual (Private Instance)
####This method is more reliable, but harder to set up.
Simply run `python3 -m pip install -U -r requirements.txt` to install all the dependencies of this bot.
Next, you'll need to create a bot account on Discord and get your bot authentication token. Create a new file called `btoken.py` in the same folder as `goldmine.py`, and insert the following:
```python
bot_token = 'INSERT_YOUR_TOKEN_HERE'
```
Replace INSERT_YOUR_TOKEN_HERE with your actual token. Make sure you keep the quotes, though!

####Now simply run `python3 goldmine.py` and your bot is good to go!
