# -*- coding: utf-8 -*-
'''
new Env('快乐红包');
27 12 * * * jd_klhb.py
版本：20261112
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) or '.')
from _boot import run
run(__file__)
