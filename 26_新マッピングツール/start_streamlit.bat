@echo off
chcp 65001
cd /d "%~dp0"

echo ======================================
echo EJ-rBOM Mapping Streamlit App
echo Port: 8504
echo ======================================

REM 本番環境とテスト環境でvenvを切り替え
if exist "D:\py\EJ_rBOM_mapping\venv\Scripts\activate.bat" (
    echo [本番環境] D:\py\EJ_rBOM_mapping\venv を使用
    call "D:\py\EJ_rBOM_mapping\venv\Scripts\activate.bat"
) else (
    echo [テスト環境] C:\Dev\90_tools\09_EJ_rBOM_マッピング２\venv を使用
    call "C:\Dev\90_tools\09_EJ_rBOM_マッピング２\venv\Scripts\activate.bat"
)

REM Streamlit起動
streamlit run app.py --server.port 8504

pause
