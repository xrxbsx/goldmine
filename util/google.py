"""Google search tools."""
import os
import random
import asyncio
from urllib.parse import quote_plus, urlparse, parse_qs
import aiohttp
import async_timeout
from bs4 import BeautifulSoup
from convert_to_old_syntax import cur_dir

url_home = "https://www.google.com/"

async def get_page(url, user_agent='Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)'):
    """Fetch the contents of an url."""
    async with aiohttp.ClientSession(loop=asyncio.get_event_loop()) as session:
        with async_timeout.timeout(8):
            async with session.get(url, headers={'User-Agent': user_agent}) as resp:
                return await resp.text()

async def filter_result(link):
    try:
        # Valid results are absolute URLs not pointing to a Google domain
        # like images.google.com or googleusercontent.com
        o = urlparse(link, 'http')
        if o.netloc and 'google' not in o.netloc:
            return link
        # Decode hidden URLs.
        if link.startswith('/url?'):
            link = parse_qs(o.query)['q'][0]
            # Valid results are absolute URLs not pointing to a Google domain
            o = urlparse(link, 'http')
            if o.netloc and 'google' not in o.netloc:
                return link
    except Exception:
        pass
    return None
async def search(query, num=3):
    url_t = url_home + 'search?hl=en&q=%(query)s&num=%(num)d&btnG=Google+Search&tbs=0&safe=off&tbm='
    query = quote_plus(query)
    ret = []
    html = await get_page(url_t % vars())
    hashes = set()
    soup = BeautifulSoup(html, 'html.parser')
    anchors = soup.find(id='search').findAll('a')
    for a in anchors:
        # Get the URL from the anchor tag.
        try:
            link = a['href']
        except KeyError:
            continue
        # Filter invalid links and links pointing to Google itself.
        link = await filter_result(link)
        if not link:
            continue
        # Discard repeated results.
        h = hash(link)
        if h in hashes:
            continue
        hashes.add(h)
        ret.append(link)
    return ret
