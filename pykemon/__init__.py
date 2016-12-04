#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Dragon5232'
__version__ = '0.3.0'
__copyright__ = 'Copyright Paul Hallett & Dragon5232 2016'
__license__ = 'BSD'

from .api import get
from .exceptions import ResourceNotFoundError

"""Pykemon

A Python wrapper for PokeAPI (http://pokeapi.co)

Usage:
> import pykemon
> pykemon.get(pokemon='bulbasaur')
<Pokemon - Bulbasaur>
> pykemon.get(pokemon_id=151)
<Pokemon - Mew>"""
