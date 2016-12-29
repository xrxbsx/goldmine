#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pykemon.request
This is the request factory for pykemon.
All API calls made to the PokeAPI website go from here."""

import asyncio
import util.json as json
import aiohttp
import async_timeout
from .models import Pokemon, Move, Type, Ability, Egg, Description, Sprite, Game
from .exceptions import ResourceNotFoundError

base_uri = 'http://pokeapi.co/api/v1'
try:
    from d_props import poke_uri
    base_uri = poke_uri
except ImportError:
    pass

endpoints = ['pokedex', 'pokedex_id', 'pokemon', 'pokemon_id', 'move', 'move_id',
             'ability', 'ability_id', 'type', 'type_id', 'egg',
             'egg_id', 'description', 'description_id', 'sprite',
             'sprite_id', 'game', 'game_id']
classes = {
    'pokemon': Pokemon,
    'move': Move,
    'type': Type,
    'ability': Ability,
    'egg': Egg,
    'description': Description,
    'sprite': Sprite,
    'game': Game
}


async def _request(uri):
    """Just a wrapper around the http library"""

    async with aiohttp.ClientSession(loop=asyncio.get_event_loop()) as session:
        with async_timeout.timeout(10):
            async with session.get(uri) as r:
                if r.status == 200:
                    txt = await r.text()
                    return await _to_json(txt)
                else:
                    raise ResourceNotFoundError(
                        'API responded with error code %s' % str(r.status))

async def _to_json(data):
    try:
        content = json.loads(data)
        return content
    except json.JSONDecodeError:
        raise json.JSONDecodeError('Error decoding data', data, 0)


async def _compose(choice):
    """Figure out exactly what resource we're requesting and return the correct
    class."""
    nchoice = list(choice.keys())[0]
    id = list(choice.values())[0]

    if '_id' in nchoice:
        nchoice = nchoice[:-3]
    return ('/'.join([base_uri, nchoice, str(id), '']), nchoice)


async def make_request(choice):
    """
    The entry point from pykemon.api.
    Call _request and _compose to figure out the resource / class
    and return the correct constructed object
    """
    uri, nchoice = await _compose(choice)
    data = await _request(uri)

    resource = classes[nchoice]
    return resource(data)
