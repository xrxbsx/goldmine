"""JSON importing abstraction layer."""

try:
    from rapidjson import *
except ImportError:
    try:
        from ujson import *
    except ImportError:
        try:
            from simplejson import *
        except ImportError:
            from json import *
