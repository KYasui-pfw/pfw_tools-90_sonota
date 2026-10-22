---
出典: 福原つながるプロジェクト_課題管理表.xlsm の「課題」シート No.398
シート: 課題
番号: No.398
区分: 課題
件名: rBOM_EXEフォルダ内に不要なファイルがありCドライブを圧迫する
発生部門: インフラ
発生日: 2026-09-01
完了日: 2026-10-16
状況: 完了
---
# 課題No.398 rBOM_EXEフォルダ内に不要なファイルがありCドライブを圧迫する

## 内容

rBOM_EXEフォルダ内に不要なファイルがありCドライブを圧迫する

## 対処・対策・回答案

2026/10/15 PFW○○
クローズで問題ありません。
※調査のため、しばらくの間RBOM.batを以下のようにさせていただこうと思います。
よろしくお願いします。

@echo off
setlocal

rem --- 1. カレントディレクトリの移動 ---
cd /d "%~dp0"

rem --- 2. ファイル一覧・タイムスタンプ調査ログの出力 ---
set "OUTPUT_DIR=\\fsrv24\TempFile\dmp_check"
if exist "%OUTPUT_DIR%" (
    rem 日時・サイズ・ファイル名を一覧化して端末名.txtに出力（上書き）
    dir /-C /T:W > "%OUTPUT_DIR%\%COMPUTERNAME%.txt" 2>nul
)

rem --- 3. 既存の環境変数設定 ---
set ORA_PATH=%CD%\instantclient_12c
set PATH=%ORA_PATH%;%PATH%
set ORACLE_HOME=%ORA_PATH%
set TNS_ADMIN=%ORA_PATH%
set ORACLE_SID=RBOMPDB
set NLS_LANG=JAPANESE_JAPAN.JA16SJISTILDE

rem --- 4. アプリケーション起動 ---
start rbom.exe

endlocal

2026/9/30 ○○
No.380導入後、今しばらく見ていただいたうえで、再度該当の圧迫問題が発生した際に、再度調査させていただく形として、一旦この課題をクローズとさせていただきたいのですがよろしいでしょうか。

2026/9/15　○○
No.380の対応で解消する可能性があるため、No.380の導入後に再確認いただく

2026/09/01　○○
rBOMフォルダ内のinstantclientのバージョンが12cであることが問題となっている可能性有。現在確認中です。

## 結果（クローズ時）

2026/10/16 打合せ
打合せにてクローズ
