@echo off
REM machine_data_extract.bat
REM PostgreSQL データ取得 → FastAPI送信 統合処理の実行バッチファイル

cd /d %~dp0

REM 仮想環境がある場合はアクティベート（オプション）
REM if exist venv\Scripts\activate.bat (
REM     call venv\Scripts\activate.bat
REM )

echo ========================================
echo 機械データ取得→FastAPI送信 統合処理
echo ========================================
python machine_data_extract.py

REM 終了コードを返す

exit /b %ERRORLEVEL%
