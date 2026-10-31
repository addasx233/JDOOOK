# -*- coding: utf-8 -*-
'''
new Env('圈子签到');
0 13 * * * jd_qzqd.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
