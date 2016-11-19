"""Functions for handling the Data Store."""
import os
import json

orig_store = {
    'version': 1,
    'date_format': '{0}/{1}/{2}',
    'quote_format': '#{0}: "{1}" — {2} [{3}]',
    'quotes': [
        {
            'id': 0,
            'quote': 'Living well is the best revenge.',
            'author': 'George Herbert',
            'date': [4, 3, 1593]
        },
        {
            'id': 1,
            'quote': 'Change your thoughts and you change your world.',
            'author': 'Norman Vincent Peale',
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
        storefile.write(json.dumps(newstore, indent=4, separators=(',', ': ')))

async def reset():
    """Reset the data store to the stock values."""
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'storage.json'), 'w') as storefile:
        storefile.write(json.dumps(orig_store, indent=4, separators=(',', ': ')))

async def read(*depths):
    """Read a specific entry or entry hierarchy from the data store."""
    pass

def initialize():
    """Initialize the data store, if needed."""
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'storage.json'), 'w+') as storefile:
        try:
            if json.loads('' + storefile.read()) == {}:
                storefile.write(json.dumps(orig_store, indent=4, separators=(',', ': ')))
        except json.decoder.JSONDecodeError:
            storefile.write(json.dumps(orig_store, indent=4, separators=(',', ': ')))
