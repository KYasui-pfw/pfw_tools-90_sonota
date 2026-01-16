@echo off
chcp 65001 > nul
setlocal

echo ============================================================
echo EJ受入 → rBOM送信 処理開始
echo ============================================================
echo.

REM --- 設定 ---
set SCRIPT_DIR=%~dp0
set WORK_DIR=%SCRIPT_DIR%work
set PYTHON=C:\Dev\90_tools\09_EJ_rBOM_マッピング２\venv\Scripts\python.exe

REM --- mapping.db のパス ---
REM 本番環境
REM set MAPPING_DB_SRC=D:\py\EJ_rBOM_mapping_2\mapping.db
REM 開発環境
set MAPPING_DB_SRC=C:\Dev\90_tools\29_rBOM自動受入\Files\mapping.db

REM --- 1. mapping.db をworkフォルダにコピー ---
echo [1] mapping.db をコピー中...
if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"
copy /Y "%MAPPING_DB_SRC%" "%WORK_DIR%\mapping.db"
if errorlevel 1 (
    echo [ERROR] mapping.db のコピーに失敗しました
    pause
    exit /b 1
)
echo [OK] mapping.db をコピーしました
echo.

REM --- 2. EJ受入データ変換 ---
echo [2] EJ受入データ変換 実行中...
"%PYTHON%" "%SCRIPT_DIR%01_EJ受入データ変換.py"
if errorlevel 1 (
    echo [ERROR] 01_EJ受入データ変換.py でエラーが発生しました
    pause
    exit /b 1
)
echo [OK] EJ受入データ変換 完了
echo.

REM --- 3. 送信データ作成 ---
echo [3] 送信データ作成 実行中...
"%PYTHON%" "%SCRIPT_DIR%02_送信データ作成.py"
if errorlevel 1 (
    echo [ERROR] 02_送信データ作成.py でエラーが発生しました
    pause
    exit /b 1
)
echo [OK] 送信データ作成 完了
echo.

REM --- 4. 送信データフィルタリング ---
echo [4] 送信データフィルタリング 実行中...
"%PYTHON%" "%SCRIPT_DIR%03_送信データフィルタリング.py"
if errorlevel 1 (
    echo [ERROR] 03_送信データフィルタリング.py でエラーが発生しました
    pause
    exit /b 1
)
echo [OK] 送信データフィルタリング 完了
echo.

REM --- 5. rBOM受入送信 ---
REMecho [5] rBOM受入送信 実行中...
REM"%PYTHON%" "%SCRIPT_DIR%04_rBOM受入送信.py"
REMif errorlevel 1 (
REM    echo [ERROR] 04_rBOM受入送信.py でエラーが発生しました
REM    pause
REM    exit /b 1
REM)
REMecho [OK] rBOM受入送信 完了
REMecho.

echo ============================================================
echo 全処理完了
echo ============================================================
pause
