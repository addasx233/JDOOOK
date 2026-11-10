# -*- coding: utf-8 -*-
'''
new Env('京东特价');
27 11 * * * jd_jdtj.py
版本：20261110
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
