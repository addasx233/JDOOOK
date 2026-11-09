# -*- coding: utf-8 -*-
'''
new Env('排行榜做任务');
34 13 * * * jd_rankVote.py
版本：20261109
'''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
from _boot import run
run(__file__)
