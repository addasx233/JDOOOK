# -*- coding: utf-8 -*-
'''
new Env('京豆拍卖');
18 10 * * * jd_jdpm.py
版本：20261110
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
