@echo off
cd /d "%~dp0"
call .\.venv312\Scripts\activate.bat
python app\main.py
pause
