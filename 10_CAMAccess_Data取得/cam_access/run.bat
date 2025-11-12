@echo off
chcp 65001 >nul
echo ======================================================
echo Access データベース → CSV 抽出処理
echo ======================================================
echo.

REM ステップ1: ファイルコピー
call copy_files.bat
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo エラー: ファイルコピーに失敗しました
    pause
    exit /b 1
)

echo.
echo ======================================================
echo Dockerコンテナを起動してCSV抽出を実行します...
echo ======================================================
echo.

REM ステップ2: Docker実行
docker run --rm ^
  -v "%~dp0data:/app/data" ^
  -v "%~dp0output:/app/output" ^
  access-to-csv

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================
    echo すべての処理が完了しました
    echo 出力先: %~dp0output
    echo ======================================================
) else (
    echo.
    echo エラー: Docker実行に失敗しました
)

echo.
pause
