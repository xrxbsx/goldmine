#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""OpusLib Package."""

__author__ = 'Dragon5232'
__copyright__ = 'Copyright (c) 2012, SvartalF'
__license__ = 'BSD 3-Clause License'

import os
import ctypes

from ctypes.util import find_library

lib_location = find_library('opus')

if lib_location is None:
    lib_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'libopus.dll')

libopus = ctypes.CDLL(lib_location)

c_int_pointer = ctypes.POINTER(ctypes.c_int)
c_int16_pointer = ctypes.POINTER(ctypes.c_int16)
c_float_pointer = ctypes.POINTER(ctypes.c_float)
