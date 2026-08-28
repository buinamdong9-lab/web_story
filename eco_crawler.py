#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Root convenience proxy for scripts/crawlers/eco_crawler.py"""
import os, sys
script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'crawlers', 'eco_crawler.py')
if __name__ == '__main__':
    os.execv(sys.executable, [sys.executable, script_path] + sys.argv[1:])
