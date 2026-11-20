# -*- coding: utf-8 -*-
'''
new Env('拍拍二手自营');
47 14 * * * jd_ppes.py
版本：20261120
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
