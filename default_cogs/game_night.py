"""Game night!"""
import asyncio
import discord
import util.commands as commands
from util.perms import or_check_perms
from .cog import Cog

class GameNight(Cog):
    """Now's your chance to have a quick and easy game night!"""
    def __init__(self, bot):
        self.games = {}
        super().__init__(bot)

    @commands.group(pass_context=True, aliases=['game_night'])
    async def gamenight(self, ctx):
        """Game night!
        Syntax: gamenight {stuff}"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @gamenight.command(pass_context=True, aliases=['end', 'finish'])
    async def stop(self, ctx):
        """Stop the current game night session.
        Usage: gamenight stop"""
        await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages', 'manage_roles'])
        if ctx.message.channel.id in self.games:
            game = self.games[ctx.message.channel.id]
            if game['role']:
                try:
                    await self.bot.delete_role(ctx.message.server, game['role'])
                except discord.Forbidden:
                    pass
            del self.games[ctx.message.channel.id]
            await self.bot.say('**Ended the current game night session at round ' + str(game['round']) + '.**')
            del game
        else:
            await self.bot.reply('there\'s no game night session active here!')

    @gamenight.command(pass_context=True, aliases=['meme_war', 'meme-war', 'memes', 'meme', 'mwar', 'memwar'])
    async def memewar(self, ctx, *, topic: str):
        """Start a meme war on a topic.
        Usage: gamenight memewar [topic]"""
        await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages', 'manage_roles'])
        game = {
            'active': False,
            'topic': topic,
            'duration': 1.5 * 60,
            'players': {
                ctx.message.author: 0
            },
            'recruiting': True,
            'role': None,
            'round': 1,
            'round_active': False,
            'r_mention': ''
        }
        self.games[ctx.message.channel.id] = game
        await self.bot.say(f''':clap: Now hosting a **meme war** for `{topic}`! :clap:
We need at least 4 participants. ({ctx.message.author.mention} is already in.)
Everyone, you have 1 minute to join! Just use `{ctx.prefix}gamenight join`.''')
        await asyncio.sleep(60)
        game['recruiting'] = False
        r_mention = ''
        if len(game['players']) >= 4:
            await self.bot.say('⚠ **Stopped due to insufficent number of participants.**')
            del self.games[ctx.message.channel.id]
            return
        try:
            role = await self.bot.create_role(ctx.message.server, name='Game Night Player', color=discord.Color.dark_teal(), mentionable=True)
            for player in game['players']:
                await self.bot.add_roles(player, role)
            r_mention = '<@&' + role.id + '> '
        except discord.Forbidden:
            await self.bot.say('⚠ **I work best with the Manage Roles permission.**')
        game['r_mention'] = r_mention
        await self.bot.say('''Starting the **meme war** in 30 seconds!
{}Get your butts in here, and grab your dankest memes!'''.format(r_mention))
        await asyncio.sleep(28.6)
        game['active'] = True
        game['round_active'] = True
        await self.bot.say(f'''{r_mention}The **meme war** is now starting for the topic `{topic}`!
Get your memes in already! :clap::clap:
Leaders: when you're ready, select a winner (and end the round) with `{ctx.prefix}gamenight winner`!''')

    @gamenight.command(pass_conext=True)
    async def topic(self, ctx, *, topic: str):
        """Start the current round with a topic."""
        await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages', 'manage_roles'])
        if ctx.message.channel.id in self.games:
            try:
                await self.bot.delete_message(ctx.message)
            except discord.Forbidden:
                await self.bot.say('⚠ **I work best with the Manage Messages permission.**')
            game = self.games[ctx.message.channel.id]
            r_mention = game['r_mention']
            game['topic'] = topic
            await self.bot.say('''Starting **round {}** in 30 seconds!
{}Get your butts in here, and grab your dankest memes!'''.format(str(game['round']), r_mention))
            await asyncio.sleep(28.6)
            game['active'] = True
            game['round_active'] = True
            await self.bot.say(f'''{r_mention}The **meme war** is now starting for the topic `{topic}`!
Get your memes in already! :clap::clap:
Leaders: when you're ready, select a winner (and end the round) with `{ctx.prefix}gamenight winner`!''')
        else:
            await self.bot.reply('there isn\'t a game night session in this channel!')

    @gamenight.command(pass_context=True)
    async def winner(self, ctx, *, winner: discord.Member):
        """Select a winner for a game night session.
        Usage: gamenight winner [winner]"""
        await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages', 'manage_roles'])
        if ctx.message.channel.id in self.games:
            try:
                await self.bot.delete_message(ctx.message)
            except discord.Forbidden:
                await self.bot.say('⚠ **I work best with the Manage Messages permission.**')
            game = self.games[ctx.message.channel.id]
            if winner in game['players']:
                k = '.'
                key = '**...and the winner is'
                msg = await self.bot.say(key + '**')
                for i in range(1, 4):
                    await asyncio.sleep(0.96)
                    await self.bot.edit_message(msg, key + (k * i) + '**')
                await asyncio.sleep(0.97)
                await self.bot.edit_message(msg, key + '...:drum:**')
                await asyncio.sleep(0.97)
                await self.bot.edit_message(msg, key + '...:drum: ' + str(winner) + '!**')
                game['players'][winner] += 1
                game['round'] += 1
                game['round_active'] = False
                await asyncio.sleep(0.6)
                await self.bot.say(f'Leaders: to set the topic for the next round, do `{ctx.prefix}gamenight topic [topic]`!')
            else:
                await self.bot.reply('that person isn\'t in this game night session!')
        else:
            await self.bot.reply('there isn\'t a game night session in this channel!')

    @gamenight.command(pass_context=True)
    async def join(self, ctx):
        """Join the current channel's game night session.
        Usage: gamenight join"""
        if ctx.message.channel.id in self.games:
            game = self.games[ctx.message.channel.id]
            if game['recruiting']:
                if ctx.message.author in game:
                    await self.bot.reply('you\'re already in the game night session! **ALLOWING FOR DEV TESTING PURPOSES**')
                    game['players'][ctx.message.author] = 0
                else:
                    game['players'][ctx.message.author] = 0
                    await self.bot.reply('you\'ve joined the game night session!')
            else:
                await self.bot.reply('it\'s too late to join this game night session!')
        else:
            await self.bot.reply('there isn\'t a game night session in this channel!')

    @gamenight.command(pass_context=True)
    async def start(self, ctx):
        await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages', 'manage_roles'])
        await self.bot.say(':clap:')

def setup(bot):
    c = GameNight(bot)
    bot.add_cog(c)
