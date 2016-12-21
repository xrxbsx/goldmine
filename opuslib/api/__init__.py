#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""OpusLib Package."""

__author__ = 'Dragon5232'
__copyright__ = 'Copyright (c) 2012, SvartalF'
__license__ = 'BSD 3-Clause License'

import os
import sys
import ctypes

from ctypes.util import find_library

lib_location = find_library('opus')

if lib_location is None:
    lib_location = os.path.join(os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__)), 'libopus.dll')

libopus = ctypes.CDLL(lib_location)

c_int_pointer = ctypes.POINTER(ctypes.c_int)
c_int16_pointer = ctypes.POINTER(ctypes.c_int16)
c_float_pointer = ctypes.POINTER(ctypes.c_float)

strerror = libopus.opus_strerror
strerror.argtypes = (ctypes.c_int,)
strerror.restype = ctypes.c_char_p
strerror.__doc__ = 'Converts an opus error code into a human readable string'

get_version_string = libopus.opus_get_version_string
get_version_string.argtypes = None
get_version_string.restype = ctypes.c_char_p
get_version_string.__doc__ = 'Gets the libopus version string'
