# -*- coding: utf-8 -*-
'''
new Env('礼享派抽奖');
8 13 * * * jd_lxp.py
版本：20261119
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
