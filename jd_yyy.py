# -*- coding: utf-8 -*-
'''
new Env('摇一摇得京豆');
0 20 * * * jd_yyy.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
