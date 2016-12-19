"""JSON importing abstraction layer."""

try:
    from rapidjson import *
except ImportError:
    try:
        from ujson import *
    except ImportError:
        from json import *
