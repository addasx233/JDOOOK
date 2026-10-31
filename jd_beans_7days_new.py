# -*- coding: utf-8 -*-
'''
new Env('豆子7天统计');
6 21 * * * jd_beans_7days_new.py
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
