#!/bin/bash

echo "======================================================"
echo "Access データベース → CSV 抽出処理"
echo "======================================================"
echo ""

# スクリプトのディレクトリを取得
SCRIPT_DIR=$(cd $(dirname "$0") && pwd)

# ステップ1: ファイルコピー
bash "$SCRIPT_DIR/copy_files.sh"
if [ $? -ne 0 ]; then
    echo ""
    echo "エラー: ファイルコピーに失敗しました"
    exit 1
fi

echo ""
echo "======================================================"
echo "Dockerコンテナを起動してCSV抽出を実行します..."
echo "======================================================"
echo ""

# ステップ2: Docker実行
docker run --rm \
  -v "$SCRIPT_DIR/data:/app/data" \
  -v "$SCRIPT_DIR/output:/app/output" \
  access-to-csv

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================"
    echo "すべての処理が完了しました"
    echo "出力先: $SCRIPT_DIR/output"
    echo "======================================================"
else
    echo ""
    echo "エラー: Docker実行に失敗しました"
    exit 1
fi
