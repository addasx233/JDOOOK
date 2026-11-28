# -*- coding: utf-8 -*-
'''
new Env('能源工坊');
18 8 * * * jd_nygf.py
版本：20261128
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
