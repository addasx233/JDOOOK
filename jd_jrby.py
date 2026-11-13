# -*- coding: utf-8 -*-
'''
new Env('京融捕鱼');
8 10 * * * jd_jrby.py
版本：20261113
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
