@echo off
chcp 65001
echo ロット番号マッピングツールを起動しています...
echo.

REM Streamlitアプリケーションの起動
streamlit run app.py --server.headless true --server.port 8511

pause
