@echo off
chcp 65001 >nul
cd /d "D:\1 кодинг\1 ПРОЕКТЫ\парсер вакансий"
set PYTHONIOENCODING=utf-8
".venv\Scripts\python.exe" lead_radar.py >> radar_log.txt 2>&1
