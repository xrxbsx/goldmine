# Goldmine
<a href="https://discord.gg/RkFgnUt"><img src="https://discordapp.com/api/guilds/239772188649979904/widget.png?" alt="Goldmine Support"></a>

This is Goldmine, a new bot for Discord that keeps things nice and snug.
Featuring VOICE (MUSIC), NATURAL LANGUAGE, IMAGES, CUSTOM WIDGETS, RANKS, and more!
This bot is written in Python 3, and uses discord.py and asyncio for enhanced performance.
###Warning: Work In Progress!

# Features
- Rich help
- Many details
- Pokemon!
- Commands:
 - purge [channel] - Removes all messages sent by this bot in the specified channel.
 - Too many more to list.
- Auto-conversation: start a friendly conversation with the bot!
 - Mentions work
 - You can also initiate it like `goldmine heya there, you awake?` and it triggers auto-conversation.
 - Auto-conversations apply per-user and per-channel, which means they won't interfere with other stuff - yay!
 - Dynamic bot names
- DM conversations: have some fun here :)
- Per-server bot name and command prefix :D
- Too many more to list.

# Installation
###Two-Click (Public Instance)
####This method is extremely easy, but may not offer the best performance and/or reliability. Overall, better.
Just click this link: [Click to add GOLDMINE and CO. to your server](https://discordapp.com/api/oauth2/authorize?client_id=239775420470394897&scope=bot&permissions=66321471 "Click to add GOLDMINE to your server!"), select a server, click **Done**, and you're all set! Easy as pie :)

You might want to set the command prefix and/or bot name for your server.
To do so, simply make sure you're a server admin (Manage Server permission), and type: 
 - `!setprop bot_name MyAwesomeBot` for bot name, replacing **MyAwesomeBot** with your desired name.
 - `!prefix $` for command prefix, replacing **$** with your desired prefix.

###Manual (Private Instance) (Selfbot mode available)
####This method is more reliable, but harder to set up. It's also required for selfbot mode.
Simply run `python3 -m pip install -U -r requirements.txt` to install all the basic dependencies of this bot. 
For many more advanced features and speed improvements, use `python3 -m pip install -U -r full_requirements.txt` (this doesn't work on Windows!).
For as much as you can get on Windows, use `python3 -m pip install -U -r win_requirements.txt`.

Now, you'll want to replace the owner with your DiscordTag.
To do this, open `properties.py` in a text editor and edit `bot_owner = '160567046642335746'` to match your Discord user ID.
Example: 012345678901234567 - make sure you don't leave out any numbers, though.
There should be 18 of them.

The bot will guide you through the setup, including login (token or email+password),
bot owner (soon), and all that good stuff.

####Simply run `python3 goldmine.py` to complete the rest of the setup! This works for both bot mode and selfbot mode.
