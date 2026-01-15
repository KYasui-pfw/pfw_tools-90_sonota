@echo off
chcp 65001 > nul
echo KRD データ管理画面を起動します...
echo.
echo URL: http://localhost:8509
echo.
echo 終了するには Ctrl+C を押してください
echo.

cd /d %~dp0
streamlit run app.py --server.port 8509
pause
