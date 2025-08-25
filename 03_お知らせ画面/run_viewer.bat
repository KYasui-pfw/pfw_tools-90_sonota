@echo off
cd /d "%~dp0"
echo Starting Notice Viewer (閲覧専用画面)...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements if not already installed
echo Installing requirements...
pip install -r requirements.txt

REM Run Streamlit viewer app
echo Starting Streamlit viewer app...
streamlit run viewer.py

pause