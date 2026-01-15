@echo off
chcp 65001 > nul
cd /d "%~dp0"
python asp_kakou_mapping.py
