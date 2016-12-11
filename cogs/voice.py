"""Definition of the bot's Voice module.'"""
import asyncio
import io
import random
import subprocess
import re
import textwrap
import discord
import util.commands as commands
import aiohttp
import async_timeout
from gtts_token import gtts_token
from util.const import sem_cells
import util.datastore as store
from .cog import Cog

class VoiceEntry:
    """Class to represent an entry in the standard voice quene."""
    def __init__(self, message, player, jukebox):
        self.requester = message.author
        self.channel = message.channel
        self.player = player
        self.jukebox = jukebox

    def __str__(self):
        fmt = '**{0}**'
        p = self.player
        tags = []
        if p.title == 'translate_tts':
            fmt = fmt.format('Speech line :smiley:')
        else:
            fmt = fmt.format(p.title)
        if p.uploader:
            tags.append('uploader *{0}*'.format(p.uploader))
        if self.requester:
            tags.append('requester *{0}*'.format(self.requester.display_name))
        if p.duration:
            tags.append('duration *{0[0]}m, {0[1]}s*'.format(divmod(p.duration, 60)))
        if tags:
            fmt += ' - ' + ', '.join(tags)
        return fmt

class SpeechEntry:
    """Class to represent an entry in the speech voice quene."""
    def __init__(self, player):
        self.player = player

class VoiceState:
    """Class for handling any voice-related actions."""
    def __init__(self, bot):
        self.current = None
        self.currents = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.play_next_speech = asyncio.Event()
        self.songs = asyncio.Queue()
        self.speeches = asyncio.Queue()
        self.skip_votes = set() # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())
        self.speech_player = self.bot.loop.create_task(self.speech_player_task())

    def is_playing(self):
        """Check if anything is currently playing."""
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        """Get the current player object."""
        return self.current.player

    @property
    def players(self):
        """Get the current speech player object."""
        return self.currents.player

    def skip(self):
        """Skip the currently playing song."""
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        """Play the next song in quene."""
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    def toggle_next_speech(self):
        """Play the next speech line in quene."""
        self.bot.loop.call_soon_threadsafe(self.play_next_speech.set)

    async def audio_player_task(self):
        """Handle the quene and playing of voice entries."""
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            if self.current.jukebox:
                if not re.match(r'http:\/\/[A-Z0-9\-]*.acapela-group.com\/MESSAGES\/[0-9]{33,}\/AcapelaGroup_WebDemo_HTML\/sounds\/[0-9]{6,10}_[a-z0-9]{10,15}\.mp3', self.current.player.url):
                    k_str = 'JUKEBOX FOR **' + self.current.player.title + '**\n'
                    juke_m = await self.bot.send_message(self.current.channel, k_str)
                    juke_cells = [':red_circle:', ':large_blue_circle:', ':green_heart:', ':diamond_shape_with_a_dot_inside:']
                    sq_dia = 9
                    while not self.play_next_song.is_set(): # :red_circle: :large_blue_circle: :green_heart:
                        lines = []
                        for i in range(sq_dia):
                            cells = []
                            for i in range(sq_dia):
                                cells.append(random.choice(sem_cells))
                            lines.append(' '.join(cells))
                        await self.bot.edit_message(juke_m, k_str + '\n'.join(lines))
                        await asyncio.sleep(1.05)
                    await self.bot.edit_message(juke_m, juke_m.content + '\nSorry, nothing here anymore!\n**FINISHED PLAYING SONG!**')
            else:
                await self.play_next_song.wait()

    async def speech_player_task(self):
        """Handle the quene and playing of speech entries."""
        while True:
            self.play_next_speech.clear()
            self.currents = await self.speeches.get()
            self.currents.player.start()
            await self.play_next_speech.wait()

class Voice(Cog):
    """Voice related commands.
    Works in multiple servers at once.
    """
    def __init__(self, bot):
        self.voice_states = {}
        self.tokenizer = gtts_token.Token()
        super().__init__(bot)

    def get_voice_state(self, server):
        """Get the current VoiceState object."""
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        """Create a new voice client on a specified channel."""
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                state.speech_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(no_pm=True)
    async def join(self, *, channel: discord.Channel):
        """Joins a voice channel.
        Syntax: join [channel]"""
        try:
            await self.create_voice_client(channel)
        except discord.InvalidArgument:
            await self.bot.say('That\'s not a voice channel!')
        except discord.ClientException:
            await self.bot.say('Already in a voice channel.')
        else:
            await self.bot.say('Ready to play audio in **' + channel.name + '**!')

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel.
        Syntax: summon"""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say('You aren\'t in a voice channel.')
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)

        return True

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, song: str):
        """Plays a song.
        Adds the requested song to the playlist (quene) for playing.
        This command automatically searches from sites like YouTube.
        The list of supported sites can be found here:
        https://rg3.github.io/youtube-dl/supportedsites.html
        Syntax: play [song/video name]
        """
        state = self.get_voice_state(ctx.message.server)
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        state.voice.encoder_options(sample_rate=48000, channels=2)
        player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)

        player.volume = 0.7
        entry = VoiceEntry(ctx.message, player, False)
        was_empty = state.songs.empty()
        await state.songs.put(entry)
        if was_empty:
            await self.bot.say('Quened ' + str(entry) + '!')

    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value: int):
        """Sets the volume of the currently playing song.
        Syntax: volume [percentage, 1-100]"""

        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.volume = value / 100
            await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song.
        Syntax: pause"""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the current song OR resume suspended bot features.
        Syntax: resume"""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        Syntax: stop
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()

        try:
            state.speech_player.cancel()
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
            await self.bot.say('Stopped.')
        except:
            await self.bot.say('Couldn\'t stop.')
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        Syntax: skip
        """

        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return

        voter = ctx.message.author
        if voter == state.current.requester:
            await self.bot.say('Requester of current song requested to skip - skipping song...')
            state.skip()
        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= 3:
                await self.bot.say('Skip vote passed, skipping song...')
                state.skip()
            else:
                await self.bot.say('Skip vote added, currently at [{}/3]'.format(total_votes))
        else:
            await self.bot.say('You\'ve already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Shows info about the currently played song.
        Syntax: playing"""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            skip_count = len(state.skip_votes)
            await self.bot.say('Now playing {} [skips: {}/3]'.format(state.current, skip_count))

    @commands.command(pass_context=True, no_pm=True)
    async def speak(self, ctx, *args):
        """Uses the SVOX pico TTS engine to speak a message.
        Syntax: speak [message]"""
        state = self.get_voice_state(ctx.message.server)

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        stream = io.BytesIO(subprocess.check_output(['pico2wave', '-w', '/tmp/pipe.wav', ' '.join(args)]))
        state.voice.encoder_options(sample_rate=16000, channels=1)
        player = state.voice.create_stream_player(stream)

        player.volume = 1.0
        player.start()
        await self.bot.say('Now speaking.')

    @commands.command(pass_context=True, aliases=['xmas', 'santa', 'c', 'season'])
    async def christmas(self, ctx):
        """Start the Christmas music playlist!
        Syntax: christmas|xmas|santa|c|season"""
        state = self.get_voice_state(ctx.message.server)

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        songs = [
            ('https://www.youtube.com/watch?v=NJ8U6TEO-qE', 'Jingle Bells'),
            ('https://www.youtube.com/watch?v=RPCXMTnO2Yw', 'Deck The Halls'),
            ('https://www.youtube.com/watch?v=nVMCUtsmWmQ', 'Have A Holly Jolly Christmas'),
            ('https://www.youtube.com/watch?v=g-OF7KGyDis', 'We Wish You A Merry Christmas'),
            ('https://www.youtube.com/watch?v=0byH9h1ClBY', 'Rudolph The Red Nosed Reindeer'),
            ('https://www.youtube.com/watch?v=vwHEqx_3BYE', 'Sleigh Ride'),
            ('https://www.youtube.com/watch?v=HWv72L4wgCc', 'Santa Claus Is Coming To Town'),
            ('https://www.youtube.com/watch?v=VfLf7A_-1Vw', 'Jingle Bells Rock'),
            ('https://www.youtube.com/watch?v=t3HJgCcSUqQ', 'Rockin\' Around The Christmas Tree'),
            ('https://www.youtube.com/watch?v=oyEyMjdD2uk', 'Twelve Days of Christmas'),
            ('https://www.youtube.com/watch?v=PJ2CuKgyNW0', 'Santa Claus Is Coming To Town'),
            ('https://www.youtube.com/watch?v=Wq73h6XZQGA', 'Carol Of The Bells'),
            ('https://www.youtube.com/watch?v=3mJrPgplZ1I', 'Rock The Holly')
        ]
        songc = len(songs)
        status = [
            'Starting Christmas playlist with jukebox! :tada::christmas_tree:',
            '**Quened [0/{0}] so far! Be patient :wink:**'.format(songc)
        ]
        st_msg = await self.bot.say(status[0])
        random.shuffle(songs)

        for n, i in enumerate(songs):
            player = await state.voice.create_ytdl_player(i[0], ytdl_options={'quiet': True}, after=state.toggle_next)
            player.volume = 0.75
            entry = VoiceEntry(ctx.message, player, False)
            await state.songs.put(entry)
            del status[len(status) - 1]
            status.append('Queued **{0}**! :smiley::christmas_tree:'.format(i[1]))
            status.append('**Quened *[{0}/{1}]* so far! Be patient :wink:**'.format(n + 1, songc))
            await self.bot.edit_message(st_msg, '\n'.join(status))
            await asyncio.sleep(1)
        await self.bot.say('**All Christmas songs have been quened!** :tada::santa:')

    @commands.command(pass_context=True, no_pm=True)
    async def gspeak(self, ctx, *args):
        """Uses a TTS voice to speak a message.
        Syntax: gspeak [message]"""
        state = self.get_voice_state(ctx.message.server)

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        opts = {
            'quiet': True,
            'user-agent': 'stagefright/1.2 (Linux;Android 6.0)',
            'referer': 'https://translate.google.com/'
        }
        base_url = 'http://translate.google.com/translate_tts'
        rounds = textwrap.wrap(' '.join(args), width=100)
        for intxt in rounds:
            g_args = {
                'ie': 'UTF-8',
                'q': intxt.replace(' ', '%20'),
                'tl': 'en-us',
                'client': 'tw-ob',
                'idx': '0',
                'total': '1',
                'textlen': '12',
                'tk': str(self.tokenizer.calculate_token(intxt))
            }
            await self.bot.say('Adding to voice queue:```' + intxt + '```**It may take up to *15 seconds* to quene.**')
            player = await state.voice.create_ytdl_player(base_url + '?' + '&'.join([i + '=' + g_args[i] for i in g_args]), ytdl_options=opts, after=state.toggle_next)
            player.volume = 0.75
            entry = VoiceEntry(ctx.message, player, False)
            await state.songs.put(entry)
            await self.bot.say('Queued **Speech**! :smiley:')
            await asyncio.sleep(1)

def setup(bot):
    c = Voice(bot)
    bot.add_cog(c)