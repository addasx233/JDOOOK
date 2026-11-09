# -*- coding: utf-8 -*-
'''
new Env('赚话费');
16 10 * * * jd_zhf.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
