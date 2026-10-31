# -*- coding: utf-8 -*-
'''
new Env('手机圈');
18 16 * * * jd_sjq.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
