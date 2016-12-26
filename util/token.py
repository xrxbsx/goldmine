import os
import sys
bot_token = None
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__)), 'bot_token.txt')) as f:
        bot_token = f.readlines()[0].replace('\n', '').replace('\r', '')
except OSError:
    print('''On Discord, bots need an user and token to sign in.
To make one, go to https://discordapp.com/developers/applications/@me and click the big + (Add New).
Fill in the details as you wish, then click Done. Now, click Create Bot User.
When that\'s done, click Show Token, copy it, and paste it here.''')
    bot_token = input('Bot token: ')
    print('Thanks! I\'ll be loading right up.')
    with open(os.path.join(os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__)), 'bot_token.txt'), 'w+') as f:
        f.write(bot_token)
