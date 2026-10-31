# -*- coding: utf-8 -*-
'''
new Env('手机馆');
48 11 * * * jd_sjg.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
