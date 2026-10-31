# -*- coding: utf-8 -*-
'''
new Env('东东农场');
41 7 * * * jd_mobileFarm.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
