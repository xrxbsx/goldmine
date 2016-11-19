"""Functions for handling quotes."""
import util.datastore as store

async def qrender(quote, qindex):
    """Render a quote object into a string."""
    d = quote['date']
    rstore = await store.dump()
    pdate = rstore['date_format'].format(d[0], d[1], d[2])
    return rstore['quote_format'].format(str(qindex + 1), quote['quote'], quote['author'], pdate)
