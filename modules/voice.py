import asyncio
import io
import subprocess
import discord
from discord.ext import commands
import aiohttp
import async_timeout
import re


class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = '*{0.title}* uploaded by {0.uploader} and requested by {1.display_name}'
        duration = self.player.duration
        if duration:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set() # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()

class Voice:
    """Voice related commands.
    Works in multiple servers at once.
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}
        self.loop = asyncio.get_event_loop()

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(no_pm=True)
    async def join(self, *, channel: discord.Channel):
        """Joins a voice channel."""
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.bot.say('Already in a voice channel...')
        except discord.InvalidArgument:
            await self.bot.say('This is not a voice channel...')
        else:
            await self.bot.say('Ready to play audio in ' + channel.name)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""
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
        If there is a song currently in the queue, then it is
        queued until the next song is done playing.
        This command automatically searches as well from YouTube.
        The list of supported sites can be found here:
        https://rg3.github.io/youtube-dl/supportedsites.html
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
            player.volume = 1.0
            entry = VoiceEntry(ctx.message, player)
            await self.bot.say('Enqueued ' + str(entry))
            await state.songs.put(entry)

    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value : int):
        """Sets the volume of the currently playing song."""

        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.volume = value / 100
            await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
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
        """Shows info about the currently played song."""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            skip_count = len(state.skip_votes)
            await self.bot.say('Now playing {} [skips: {}/3]'.format(state.current, skip_count))

    @commands.command(pass_context=True, no_pm=False)
    async def speak(self, ctx, *args):
        """Uses the SVOX Pico TTS engine to speak a message."""
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
        """Uses the Purple Shep TTS voice to speak a message."""
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
            player = await state.voice.create_ytdl_player(keyline, ytdl_options=opts)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 1.0
            player.start()
