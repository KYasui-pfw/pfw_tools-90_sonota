#!/bin/bash

###############################################################################
# run_all.sh
# 処理1と処理2を並列実行後、処理3・4を順次実行するラッパースクリプト
###############################################################################

SCRIPT_DIR=$(cd $(dirname "$0") && pwd)
LOG_DIR="/app/logs"

# ログディレクトリが存在しない場合は作成
mkdir -p "$LOG_DIR"

# 処理1と処理2を並列実行（バックグラウンド）
python "$SCRIPT_DIR/process1.py" &
PID1=$!
EXIT_CODE1=0

python "$SCRIPT_DIR/process2.py" &
PID2=$!

# 両方の処理が完了するまで待機
wait $PID2
EXIT_CODE2=$?

# 処理3: CSV → FastAPI completion エンドポイント送信（EJデータ）
## python "$SCRIPT_DIR/process3.py"
EXIT_CODE3=$?

# 処理4: CSV → FastAPI completion エンドポイント送信（シリンダ・ダイアルデータ）
## python "$SCRIPT_DIR/process4.py"
EXIT_CODE4=$?

# いずれかの処理が失敗した場合はエラーコードを返す
if [ $EXIT_CODE1 -ne 0 ] || [ $EXIT_CODE2 -ne 0 ] || [ $EXIT_CODE3 -ne 0 ] || [ $EXIT_CODE4 -ne 0 ]; then
    exit 1
fi

exit 0
