@echo off
echo Docker Compose でお知らせシステムを起動中...
echo.

REM Docker Composeでサービスを起動
docker-compose up -d

echo.
echo サービスが起動しました:
echo - 管理画面: http://localhost:8501
echo - 閲覧画面: http://localhost:8502
echo.
echo 停止する場合は docker-stop.bat を実行してください。

pause