# -*- coding: utf-8 -*-
'''
new Env('京豆拍卖');
0 6 * * * jd_jdpm.py
版本：20261115
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
