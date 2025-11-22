#!/bin/bash
set -e

echo "======================================================"
echo "KRD MySQL → SQLite 同期アプリケーションを起動しています..."
echo "起動時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"
echo ""

# 環境変数を読み込み
cd /app
set -a
source .env
set +a

# 起動時に1回実行
echo "[起動時処理] 同期処理を実行します..."
echo "高頻度同期（5テーブル）を実行..."
python3 /app/krd_sync_frequent.py
echo ""
echo "低頻度同期（45テーブル）を実行..."
python3 /app/krd_sync_hourly.py
echo ""

# cronをフォアグラウンドで起動
echo "cron デーモンを起動します..."
echo "  - 高頻度同期: 5分ごと"
echo "  - 低頻度同期: 1時間ごと"
echo "======================================================"
echo ""

# crontabの内容を確認
echo "登録されているcrontab:"
cat /etc/cron.d/krd-sync-cron
echo ""

# cronをフォアグラウンドで起動
exec cron -f -L 2
