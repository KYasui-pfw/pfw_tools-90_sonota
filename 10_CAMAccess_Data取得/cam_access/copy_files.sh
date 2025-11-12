#!/bin/bash

echo "======================================================"
echo "Access データベースファイルをコピーしています..."
echo "======================================================"
echo ""

# ネットワークドライブのマウントポイント（環境に応じて変更）
SOURCE1="/mnt/schejule/cylline/Cyl_pfw_table.accdb"
SOURCE2="/mnt/schejule/camline/EJ/EJ_DETA_SERVER/EJデータマスター.accdb"

# スクリプトのディレクトリを取得
SCRIPT_DIR=$(cd $(dirname "$0") && pwd)
DEST_DIR="$SCRIPT_DIR/data"

# dataディレクトリが存在しない場合は作成
if [ ! -d "$DEST_DIR" ]; then
    mkdir -p "$DEST_DIR"
    echo "dataディレクトリを作成しました: $DEST_DIR"
    echo ""
fi

# ファイル1をコピー
echo "[1/2] コピー中: $SOURCE1"
if [ -f "$SOURCE1" ]; then
    cp -f "$SOURCE1" "$DEST_DIR/"
    if [ $? -eq 0 ]; then
        echo "  ✓ コピー完了: Cyl_pfw_table.accdb"
    else
        echo "  ✗ コピー失敗: Cyl_pfw_table.accdb"
    fi
else
    echo "  ✗ ソースファイルが見つかりません"
fi
echo ""

# ファイル2をコピー
echo "[2/2] コピー中: $SOURCE2"
if [ -f "$SOURCE2" ]; then
    cp -f "$SOURCE2" "$DEST_DIR/"
    if [ $? -eq 0 ]; then
        echo "  ✓ コピー完了: EJデータマスター.accdb"
    else
        echo "  ✗ コピー失敗: EJデータマスター.accdb"
    fi
else
    echo "  ✗ ソースファイルが見つかりません"
fi
echo ""

echo "======================================================"
echo "ファイルコピーが完了しました"
echo "======================================================"
