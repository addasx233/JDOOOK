# -*- coding: utf-8 -*-
'''
new Env('好礼许愿机');
16 12 * * * jd_hlxyj.py
版本：20261127
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
