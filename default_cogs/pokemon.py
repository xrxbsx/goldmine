"""Cute little Pokémon!"""
import random
import math
import re
from collections import OrderedDict
import discord
import util.commands as commands
from util.pykemon.api import get as pokeget
from util.pykemon import ResourceNotFoundError
from util.pykemon.request import _request, Description
from .cog import Cog

class Pokemon(Cog):
    """Cute little Pokémon!"""

    @commands.command(pass_context=True, aliases=['pokeball', 'pokedex'])
    async def pokemon(self, ctx, *pokemon_name: str):
        """Get the info about a Pokémon!
        Usage: pokemon {name or id}"""
        bot = self.bot
        d_lines = []
        if pokemon_name:
            p_name = pokemon_name.lower()
            try:
                if re.match(r'[0-9]+', p_name):
                    target = await pokeget(pokemon_id=int(p_name))
                else:
                    target = await pokeget(pokemon_id=p_name)
            except (ResourceNotFoundError, ValueError):
                await bot.say('No such **pokemon**! Try a **Pokédex entry**. (Needs to be **name** or **ID**.)')
                return
        else:
            count = 709 # current count of pokemon in api v1
            target = await pokeget(pokemon_id=random.randint(1, count))
        try:
            fn_point = target.descriptions[target.name.lower() + '_gen_1']
        except KeyError:
            fn_point = random.choice(list(target.descriptions.values()))
        desc_json = await _request('http://pokeapi.co' + fn_point)
        desc = Description(desc_json)
        em_data = {
            'title': target.name.replace('-', ' '),
            'color': int('0x%06X' % random.randint(0, 256**3-1), 16)
        }
        essentials = ['Description', 'National ID', 'Health', 'Height', 'Weight', 'Attack', 'Defense', 'Type(s)']
        skipped = ['Moves', 'Effort Value Yield', 'Egg Groups', 'Total', 'Growth Rate', 'Catch Rate', 'Male-Female Ratio', 'Egg Cycles']
        beginning = ['Description', 'National ID', 'Health', 'Attack', 'Defense', 'Weight', 'Height', 'Speed', 'Special Attack', 'Special Defense', 'Experience', 'Happiness', 'Abilities']
        tw_float = float(target.weight) / 10.0
        th_float = float(target.height) / 10.0
        th_inch = th_float / .3048 % 1 * 12
        em_field_data = {
            'Description': desc.description,
            'National ID': target.id,
            'Health': str(target.hp) + ' HP',
            'Moves': ', '.join(target.moves),
            'Types(s)': ', '.join([i.title() for i in target.types]),
            'Abilities': ', '.join([i.title() for i in target.abilities]),
            'Height': str(th_float) + ' m (' + str(int(math.floor(th_inch / 12))) + ' ft ' + str(round(th_inch % 12, 2)) + ' in)',
            'Weight': str(tw_float) + ' kg (' + str(round(tw_float * 2.2, 2)) + ' lb)',
            'Growth Rate': target.growth_rate,
            'Defense': target.defense,
            'Attack': target.attack,
            'Experience': target.exp,
            'Happiness': target.happiness,
            'Egg Cycles': target.egg_cycles,
            'Catch Rate': target.catch_rate,
            'Special Attack': target.sp_atk,
            'Special Defense': target.sp_def,
            'Speed': target.speed,
            'Total': target.total,
            'Effort Value Yield': target.ev_yield,
            'Male-Female Ratio': target.male_female_ratio,
            'Egg Groups': ', '.join(target.egg_groups)
        }
        em_fields = OrderedDict(sorted(em_field_data.items(), key=lambda t: len(t[0])))
        if target.species:
            em_fields['Species'] = target.species
        if target.evolutions:
            em_fields['Evolves Into'] = ', '.join(target.evolutions)
            em_fields.move_to_end('Evolves Into', last=False)
        for i in reversed(beginning):
            em_fields.move_to_end(i, last=False)
        for key, value in em_fields.items():
            if key not in skipped:
                if key not in essentials:
                    d_lines.append(key + ': ' + str(value))
        emb = discord.Embed(**em_data, description='\n'.join(d_lines))
        for key, value in em_fields.items():
            if key in essentials:
                emb.add_field(name=key, value=value)
        emb.set_thumbnail(url='http://pokeapi.co/media/img/{0}.png'.format(str(target.id)))
        emb.set_image(url='http://pokeapi.co/media/img/{0}.png'.format(str(target.id)))
        emb.set_author(name=target.name.replace('-', ' '), icon_url='http://pokeapi.co/media/img/{0}.png'.format(str(target.id)))
        await bot.say(embed=emb)

def setup(bot):
    """Set up the cog."""
    bot.add_cog(Pokemon(bot))
