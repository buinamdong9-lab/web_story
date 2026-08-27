@echo off
chcp 65001 > nul
title Auto Crawler - Akay Truyen
cd /d "%~dp0"
echo ========================================================
echo       KHỞI ĐỘNG AUTO CRAWLER (CHẠY MỖI 6 TIẾNG)
echo ========================================================
python auto_crawler.py
pause
