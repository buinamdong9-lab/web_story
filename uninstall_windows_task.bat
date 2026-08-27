@echo off
cd /d "%~dp0"
echo Dang go bo task AkayTruyenAutoCrawler...
schtasks /delete /tn "AkayTruyenAutoCrawler" /f
echo Da go bo thanh cong.
pause
