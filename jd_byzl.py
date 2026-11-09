# -*- coding: utf-8 -*-
'''
new Env('捕鱼助力');
20 10 * * * jd_byzl.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
