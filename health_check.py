#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Root Proxy -> scripts/pipelines/health_check.py
WebStory Library Health Check Engine
"""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_TARGET_SCRIPT = os.path.join(_SCRIPT_DIR, 'scripts', 'pipelines', 'health_check.py')

if __name__ == '__main__':
    if os.path.exists(_TARGET_SCRIPT):
        sys.path.insert(0, os.path.join(_SCRIPT_DIR, 'scripts', 'pipelines'))
        import runpy
        runpy.run_path(_TARGET_SCRIPT, run_name='__main__')
    else:
        print(f"[ERROR] Target script not found: {_TARGET_SCRIPT}")
        sys.exit(1)
