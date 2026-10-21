@echo off
cd /d "%~dp0"
python servidor.py --pregunta %*
pause
