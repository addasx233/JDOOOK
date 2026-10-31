# -*- coding: utf-8 -*-
'''
new Env('晒家大赛');
8 10 * * * jd_sjds.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
