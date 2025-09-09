::############################################################
::# specifications-fit.xlsを読み込む処理
::# オートオイラー必要有無の判断に使用する（構成情報にないため）
::# 
::############################################################
::@echo off

net use \\fsrv08\ /user:administrator@pfw_design.local 1956fkthoy

set SOURCE=\\fsrv08\specifications-fit
set DEST=D:\py\hontaigr_checksheet\work\spec
set FILE_NAME=specifications-fit.xls

rem タイムスタンプが更新されているファイルのみコピー（/XO: 既存ファイルより新しいもののみコピー）
robocopy %SOURCE% %DEST% %FILE_NAME% /XO /R:3 /W:5

if %ERRORLEVEL% EQU 1 (
    python "D:\py\hontaigr_checksheet\bat\spec_update.py"
)

net use \\fsrv08\ /delete