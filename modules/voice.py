"""Definition of the bot's Voice module.'"""
import asyncio
import io
import subprocess
import re
import textwrap
import discord
from discord.ext import commands
import aiohttp
import async_timeout
from .cog import Cog

class VoiceEntry:
    """Class to represent an entry in the standard voice quene."""
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = '**{0.title}** uploaded by *{0.uploader}* and requested by *{1.display_name}*'
        duration = self.player.duration
        if duration:
            fmt = fmt + ' (length: {0[0]}m, {0[1]}s)'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

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
            await self.bot.say('This is not a voice channel...')
        except discord.ClientException:
            await self.bot.say('Already in a voice channel...')
        else:
            await self.bot.say('Ready to play audio in ' + channel.name)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel.
        Syntax: summon"""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say('You are not in a voice channel.')
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

        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as exp:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(exp).__name__, exp))
        else:
            player.volume = 0.7
            entry = VoiceEntry(ctx.message, player)
            await self.bot.say('Enqueued ' + str(entry))
            await state.songs.put(entry)

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
            state.audio_player.cancel()
            state.speech_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
        except:
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
            await self.bot.say('You have already voted to skip this song.')

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

    @commands.command(pass_context=True, no_pm=False)
    async def speak(self, ctx, *args):
        """Uses the SVOX Pico TTS engine to speak a message.
        Syntax: speak [message]"""
        state = self.get_voice_state(ctx.message.server)

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        try:
            stream = io.BytesIO(subprocess.check_output(['pico2wave', '-w', '/tmp/pipe.wav', ' '.join(args)]))
            state.voice.encoder_options(sample_rate=16000, channels=1)
            player = state.voice.create_stream_player(stream)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 1.0
            player.start()

    async def getform(self, session, url, data):
        with async_timeout.timeout(10):
            async with session.post(url, data=data) as response:
                return await response.text()

    @commands.command(pass_context=True, no_pm=False)
    async def purpleshep(self, ctx, *args):
        """Uses the Purple Shep TTS voice to speak a message.
        Note: This voice cannot speak strings higher than 300 characters.
        Syntax: purpleshep [message]"""
        state = self.get_voice_state(ctx.message.server)

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        opts = {
            'default_search': 'auto',
            'quiet': True,
        }
        intxt = ' '.join(args)

        try:
            async with aiohttp.ClientSession(loop=self.loop) as session:
                payload = {
                    'MyLanguages': 'sonid10',
                    '0': 'Leila',
                    '1': 'Laia',
                    '2': 'Eliska',
                    '3': 'Mette',
                    '4': 'Zoe',
                    '5': 'Jasmijn',
                    '6': 'Tyler',
                    '7': 'Deepa',
                    '8': 'Rhona',
                    '9': 'Rachel',
                    'MySelectedVoice': 'WillFromAfar (emotive voice)',
                    '11': 'Hanna',
                    '12': 'Sanna',
                    '13': 'Manon-be',
                    '14': 'Louise',
                    '15': 'Manon',
                    '16': 'Claudia',
                    '17': 'Dimitris',
                    '18': 'Fabiana',
                    '19': 'Sakura',
                    '20': 'Minji',
                    '21': 'Lulu',
                    '22': 'Bente',
                    '23': 'Monika',
                    '24': 'Marcia',
                    '25': 'Celia',
                    '26': 'Alyona',
                    '27': 'Biera',
                    '28': 'Ines',
                    '29': 'Rodrigo',
                    '30': 'Elin',
                    '31': 'Samuel',
                    '32': 'Kal',
                    '33': 'Mia',
                    '34': 'Ipek',
                    'MyTextForTTS': intxt,
                    't': '1',
                    'SendToVaaS': ''
                }
                rtml = await self.getform(session, 'http://www.acapela-group.com/demo-tts/DemoHTML5Form_V2.php', payload)
                keyout = re.findall("^.*var myPhpVar = .*$", rtml, re.MULTILINE)[0]
            keyline = keyout.split("'")[1]
            await self.bot.say('Now playing the following string:\n```' + ' '.join(args) + '```\n...with the Purple Shep TTS voice. Direct link to sound file:\n<' + keyline + '>\n**Note: There may be quite a *delay* before you hear the voice. Please be patient, and give it up to *15* seconds.**')
            player = await state.voice.create_ytdl_player(keyline, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 0.75
            entry = VoiceEntry(ctx.message, player)
            await self.bot.say('Enqueued ' + str(entry))
            await state.songs.put(entry)
