"""Functions for handling the Data Store."""
import os
import json

orig_store = {
    'version': 2,
    'date_format': '{0}/{1}/{2}',
    'quote_format': '**#{0}**: *"{1}"* \u2014 `{2}` [{3}]',
    'quotes': [
        {
            'id': 0,
            'quote': 'Haaaaaaaaahn!',
            'author': 'Frisky Turtle, MrXarous',
            'author_ids': ['000000000000000000', '141246933359394816'],
            'date': [11, 7, 2016]
        },
        {
            'id': 1,
            'quote': 'Living well is the best revenge.',
            'author': 'George Herbert',
            'author_ids': ['000000000000000000'],
            'date': [4, 3, 1593]
        },
        {
            'id': 2,
            'quote': 'Change your thoughts and you change your world.',
            'author': 'Norman Vincent Peale',
            'author_ids': ['000000000000000000'],
            'date': [5, 31, 1898]
        }
    ]
}

async def dump():
    """Dump the entire data store's contents.'"""
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'storage.json'), 'r') as storefile:
        return json.loads('' + storefile.read())

async def write(newstore):
    """Write a new dictionary as the data store."""
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'storage.json'), 'w') as storefile:
        storefile.write(json.dumps(newstore, indent=1, separators=(',', ':')))

async def reset():
    """Reset the data store to the stock values."""
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'storage.json'), 'w') as storefile:
        storefile.write(json.dumps(orig_store, indent=1, separators=(',', ':')))

async def read(*depths):
    """Read a specific entry or entry hierarchy from the data store."""
    pass

def initialize():
    """Initialize the data store, if needed."""
#    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'storage.json'), 'w+') as storefile:
#        try:
#            json.loads('' + storefile.read())
#        except json.decoder.JSONDecodeError:
#            storefile.write(json.dumps(orig_store, indent=1, separators=(',', ':')))
    pass