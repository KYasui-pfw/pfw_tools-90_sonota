#!/bin/bash
set -e

# 環境変数を読み込み（特殊文字対応版）
cd /app
set -a
source .env
set +a

# 起動時に1回実行
/app/scripts/run_all.sh

# cronをフォアグラウンドで起動（15分ごとに自動実行）
exec cron -f -L 2
