@echo off
rem 公開URLは IIS のリバースプロキシ経由で http://IP/名前/ 。アプリは 127.0.0.1:3000 でのみ待ち受ける
rem 共有を増やすときは SHARES に「名前=フォルダ」を ; 区切りで足す（下の例の rem を外す）。反映にはこのアプリの再起動が必要
rem （直接確認したい場合は サーバー上のブラウザで http://127.0.0.1:3000/PCOM/ を開く）
set "SHARES=PCOM=D:\Kanri\fit_order"
rem set "SHARES=%SHARES%;XXXX=D:\別のフォルダ"
set MAX_MB=0
cd /d %~dp0
venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 3000
