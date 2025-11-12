#!/bin/bash
set -e

echo "======================================================"
echo "CAM/CYL アプリケーションを起動しています..."
echo "起動時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"
echo ""

# 環境変数を読み込み（特殊文字対応版）
cd /app
set -a
source .env
set +a

# 起動時に1回実行
echo "[起動時処理] データ抽出処理を実行します..."
/app/scripts/run_all.sh
echo ""

# cronをフォアグラウンドで起動
echo "cron デーモンを起動します（15分ごとに自動実行）..."
echo "======================================================"
echo ""

# crontabの内容を確認
echo "登録されているcrontab:"
cat /etc/cron.d/camcyl-cron
echo ""

# cronをフォアグラウンドで起動
# .envファイルがcrontabから読み込まれるため、環境変数のエクスポートは不要

exec cron -f -L 2
