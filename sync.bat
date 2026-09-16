@echo off
rem Двойной клик — то же, что `python sync.py`, но окно не закрывается,
rem пока не нажмёшь клавишу: видно, что изменилось и не было ли ошибки.
chcp 65001 >nul
cd /d "%~dp0"
python sync.py
echo.
pause
