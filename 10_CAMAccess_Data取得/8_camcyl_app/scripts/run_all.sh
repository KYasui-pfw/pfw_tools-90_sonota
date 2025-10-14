#!/bin/bash

###############################################################################
# run_all.sh
# 処理1と処理2を並列実行するラッパースクリプト
###############################################################################

SCRIPT_DIR=$(cd $(dirname "$0") && pwd)
LOG_DIR="/app/logs"

echo "======================================================"
echo "CAM/CYL データ抽出処理開始"
echo "実行時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"
echo ""

# ログディレクトリが存在しない場合は作成
mkdir -p "$LOG_DIR"

# 処理1と処理2を並列実行（バックグラウンド）
echo "[並列実行] 処理1（rBOM CSV）と処理2（Access DB）を開始します..."
echo ""

# 処理1: rBOM CSVコピー・加工
python "$SCRIPT_DIR/process1.py" &
PID1=$!

# 処理2: Access DB → CSV抽出
python "$SCRIPT_DIR/process2.py" &
PID2=$!

# 両方の処理が完了するまで待機
echo "処理1 (PID: $PID1) 実行中..."
echo "処理2 (PID: $PID2) 実行中..."
echo ""

wait $PID1
EXIT_CODE1=$?

wait $PID2
EXIT_CODE2=$?

# 結果判定
echo ""
echo "======================================================"
echo "処理完了"
echo "======================================================"

if [ $EXIT_CODE1 -eq 0 ]; then
    echo "[処理1] 成功"
else
    echo "[処理1] 失敗 (Exit Code: $EXIT_CODE1)"
fi

if [ $EXIT_CODE2 -eq 0 ]; then
    echo "[処理2] 成功"
else
    echo "[処理2] 失敗 (Exit Code: $EXIT_CODE2)"
fi

echo "終了時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"

# いずれかの処理が失敗した場合はエラーコードを返す
if [ $EXIT_CODE1 -ne 0 ] || [ $EXIT_CODE2 -ne 0 ]; then
    exit 1
fi

exit 0
