"""Wrapper for everything Discord token."""
import os
import sys
from getpass import getpass
bot_token = ['']
root_dir = os.path.dirname(os.path.realpath(sys.modules['__main__'].core_file))
data_dir = os.path.join(root_dir, 'data')
self_setup_finished = False

if not os.path.exists(data_dir):
    os.makedirs(data_dir)

def self_loop():
    global self_setup_finished
    global bot_token
    email = input('Your e-mail: ')
    passwd = getpass(prompt='Your password: ')
    if ('@' in email) and ('.' in email):
        bot_token[0] = email
    else:
        print('Hmm, that e-mail doesn\'t seem right. Let\'s try again...')
        self_loop()
        return
    if len(passwd) > 1:
        bot_token = [bot_token[0], passwd]
    else:
        print('Hmm, that password doesn\'t seem right. Let\'s try again...')
        self_loop()
        return
    self_setup_finished = True
def write():
    print('Thanks! I\'ll be loading right up.')
    with open(os.path.join(root_dir, 'bot_token.txt'), 'w+') as f:
        f.write(', '.join(bot_token))
def inter_loop():
    global bot_token
    bot_token = [input('Bot token: ')]
    if bot_token[0].lower().startswith('self'):
        print('''Ok, here\'s to selfbot mode. I\'ll need your Discord e-mail and password.
It\'s normal for the password to not appear when you type it. Don\'t worry, it\'s working.
This is done for security purposes.''')
        self_loop()
        write()
        return
    else:
        if ('.' in bot_token[0]) or (self_setup_finished):
            write()
        else:
            print('Hmm, that token doesn\'t seem right. Let\'s try again...')
            inter_loop()
            return
try:
    with open(os.path.join(root_dir, 'bot_token.txt')) as f:
        bot_token = [f.readlines()[0].replace('\n', '').replace('\r', '')]
        if ', ' in bot_token[0]:
            bot_token = bot_token[0].split(', ')
except (FileNotFoundError, IndexError):
    print('''On Discord, bots need an user and token to sign in.
To make one, go to https://discordapp.com/developers/applications/@me and click the big + (Add New).
Fill in the details as you wish, then click Done. Now, click Create Bot User.
When that\'s done, click Show Token, copy it, and paste it here.
HOWEVER, if you want me to run as a selfbot, just answer \'self\' for this.''')
    try:
        inter_loop()
    except KeyboardInterrupt:
        print('\nYou pressed Ctrl-C... Ok, exiting setup.')
        exit(0)
selfbot = len(bot_token) > 1
