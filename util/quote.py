"""Functions for handling quotes."""
import asyncio

async def qrender(quote, qindex, bot):
    """Render a quote object into a string."""
    d = quote['date']
    pdate = bot.store.store['date_format'].format(d[0], d[1], d[2])
    return bot.store.store['quote_format'].format(str(qindex + 1), quote['quote'], quote['author'], pdate)
