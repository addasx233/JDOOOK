# -*- coding: utf-8 -*-
'''
new Env('交易指数');
36 15 * * * jd_jyzs.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
