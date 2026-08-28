#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Root Proxy -> scripts/pipelines/optimize_data.py
WebStory Full-Data Speed & Optimization Engine
"""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_TARGET_SCRIPT = os.path.join(_SCRIPT_DIR, 'scripts', 'pipelines', 'optimize_data.py')

if __name__ == '__main__':
    if os.path.exists(_TARGET_SCRIPT):
        # Execute target script with original arguments and python path
        sys.path.insert(0, os.path.join(_SCRIPT_DIR, 'scripts', 'pipelines'))
        import runpy
        runpy.run_path(_TARGET_SCRIPT, run_name='__main__')
    else:
        print(f"[ERROR] Target script not found: {_TARGET_SCRIPT}")
        sys.exit(1)
