import asyncio
import pykemon
loop = asyncio.get_event_loop()
print(loop.run_until_complete(pykemon.get(pokemon='bulbasaur')))
