@echo off
rem 同じフォルダの同名の .ps1（02_手配指示登録.ps1）を実行する
rem ※ ps1 のファイル名は bat 自身の名前から作る（%~dpn0）。bat の中に日本語のファイル名を書くと
rem    cmd のコードページによって化けるため。bat と ps1 の名前は必ずそろえること
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dpn0.ps1"
rem 終了コード 2 = RPA で画面が見つからず、終了処理をして終わった（エラーログ.txt に記録済み）
rem 終了コード 3 = 夜間処理の状態が取れず、実行しなかった（エラーログ.txt に記録済み）
rem どちらも止めずに終わる
if errorlevel 2 exit /b %errorlevel%
if errorlevel 1 (
    echo.
    echo エラーで終了しました。上のメッセージを確認してください。
    pause
)