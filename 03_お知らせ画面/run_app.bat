@echo off
cd /d "%~dp0"
echo Starting Notice Management System...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements if not already installed
echo Installing requirements...
pip install -r requirements.txt

REM Run Streamlit app
echo Starting Streamlit app...
python -m streamlit run app.py

pause