# -*- coding: utf-8 -*-
"""
00_Kakoudenpyo取得.py
EJサーバーからCAMKakouDenpyo.csvを取得して上書き更新
"""

import shutil
from pathlib import Path
from datetime import datetime
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ソース（EJサーバー）
SOURCE_PATH = Path(r"\\172.17.107.102\PrintOutCsv\4.加工\4-01 CAMKakouDenpyo.csv")

# 出力先
DEST_DIR = Path(r"C:\Dev\90_tools\30_工程マスタ作成\01_KakouDenpyo")
DEST_PATH = DEST_DIR / "4-01 CAMKakouDenpyo.csv"


def main():
    print("=" * 60)
    print("00_Kakoudenpyo取得")
    print(f"ソース: {SOURCE_PATH}")
    print(f"出力先: {DEST_PATH}")
    print("=" * 60)

    # ソースファイル存在確認
    if not SOURCE_PATH.exists():
        print(f"エラー: ソースファイルが見つかりません: {SOURCE_PATH}")
        return False

    # 出力先ディレクトリ確認
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # 既存ファイルの情報表示
    if DEST_PATH.exists():
        old_stat = DEST_PATH.stat()
        old_time = datetime.fromtimestamp(old_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        old_size = old_stat.st_size
        print(f"既存ファイル: {old_time}, {old_size:,} bytes")

    # ソースファイル情報
    src_stat = SOURCE_PATH.stat()
    src_time = datetime.fromtimestamp(src_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    src_size = src_stat.st_size
    print(f"ソースファイル: {src_time}, {src_size:,} bytes")

    # コピー実行
    shutil.copy2(SOURCE_PATH, DEST_PATH)

    # 確認
    if DEST_PATH.exists():
        new_stat = DEST_PATH.stat()
        new_time = datetime.fromtimestamp(new_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        new_size = new_stat.st_size
        print(f"コピー完了: {new_time}, {new_size:,} bytes")
        return True
    else:
        print("エラー: コピーに失敗しました")
        return False


if __name__ == "__main__":
    success = main()
    print("=" * 60)
    sys.exit(0 if success else 1)
