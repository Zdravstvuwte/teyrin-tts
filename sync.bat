@echo off
rem Double-click = "python sync.py", but the window stays open to show the result.
rem ASCII only: cmd misreads batch files with non-ASCII characters under UTF-8.
chcp 65001 >nul
cd /d "%~dp0"
python sync.py
echo.
pause
