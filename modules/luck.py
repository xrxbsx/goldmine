import asyncio
import io
import random

import discord
from discord.ext import commands


class Luck:
    """Commands that require some luck to use.
    Lose the coin toss for me, will you?
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def choose(self, *choices: str):
        """Chooses between choices given."""
        await self.bot.say(random.choice(choices))

    @commands.command()
    async def flipcoin(self):
        """Flips a virtual coin."""
        await self.bot.say('The coin toss revealed... ' + random.choice(['Heads', 'Tails'] + '!'))

    @commands.command()
    async def roll(self, dice: str):
        """Rolls a virtual dice in [# of rolls]d[Range: 1-N] format."""
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await self.bot.say('Format has to be in NdN!')
            return

        result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await self.bot.say(result)
