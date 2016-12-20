#!/usr/bin/env python3
import asyncio
import logging
try:
    import uvloop
    have_uvloop = True
except ImportError:
    have_uvloop = False
import discord
from token_loader import bot_token as token

logging.basicConfig(level=logging.INFO)
if have_uvloop:
    asyncio.set_event_loop(uvloop.new_event_loop())
bot = discord.Client()
bot.run(token)
