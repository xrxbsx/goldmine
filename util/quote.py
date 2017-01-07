"""Functions for handling quotes."""
from .const import quote_format

def qrender(quote, qindex, bot):
    """Render a quote object into a string."""
    d = quote['date']
    pdate = bot.store['date_format'].format(d[0], d[1], d[2])
    return quote_format.format(str(qindex + 1), quote['quote'], quote['author'], pdate, ('' if '*' in quote['quote'] else '*'))
