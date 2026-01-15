@echo off
chcp 65001 > nul
cd /d "%~dp0"
python 01_d3110_seino_count.py
python 02_hmbuncd7_kotei_check.py
python 03_t_prs_job_cd_bom_export.py
python 04_hmbuncd6_kotei_check.py
python 05_t_prs_job_cd_bom_export_hmbuncd6.py
python 06_hitsuyosu_check.py

REM ファイルハンドル解放のため少し待機
echo.
echo ファイル処理完了を待機中...
timeout /t 3 /nobreak > nul

REM outputフォルダを部品表調査としてコピー
set DEST_DIR=D:\py\perl_kakoudenpyo\17_EJ_rBOM_ASPKAKOUDEPYO_mapping\perl_denpyo\部品表調査
if exist "%DEST_DIR%" rmdir /s /q "%DEST_DIR%"
robocopy "%~dp0output" "%DEST_DIR%" /E /R:3 /W:5
if %ERRORLEVEL% LEQ 7 (
    echo コピー完了: %DEST_DIR%
) else (
    echo コピーエラー発生: %ERRORLEVEL%
)
