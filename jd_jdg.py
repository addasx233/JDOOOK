# -*- coding: utf-8 -*-
'''
new Env('JDG抽奖');
53 3 * * * jd_jdg.py
版本：20261116
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
