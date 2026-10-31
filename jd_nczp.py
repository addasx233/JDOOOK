# -*- coding: utf-8 -*-
'''
new Env('东东农场转盘');
16 9 * * * jd_nczp.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
