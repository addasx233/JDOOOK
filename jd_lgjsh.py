# -*- coding: utf-8 -*-
'''
new Env('流感季守护');
28 9 * * * jd_lgjsh.py
版本：20261127
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
