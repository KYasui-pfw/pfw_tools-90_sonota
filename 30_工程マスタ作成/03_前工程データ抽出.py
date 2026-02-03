# -*- coding: utf-8 -*-
"""
03_前工程データ抽出.py
前工程横展開(C).csvからダミーデータを除外して有効データのみ抽出

処理内容:
  1. 前工程横展開(C).csvを読み込み
  2. 「COM-」または「-COM」を含む行を削除（ダミーデータ）
  3. 有効データのみをworkフォルダに出力

入力:
  - 03_前工程/前工程横展開(C).csv

出力:
  - work/03_前工程横展開_有効データ.csv
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# 入力ファイル
INPUT_CSV = Path(r"C:\Dev\90_tools\30_工程マスタ作成\03_前工程\前工程横展開(C).csv")

# 出力先
OUTPUT_DIR = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work")
OUTPUT_CSV = OUTPUT_DIR / "03_前工程横展開_有効データ.csv"

# ダミーデータパターン
DUMMY_PATTERNS = ["COM-", "-COM"]


def contains_dummy_pattern(line: str) -> bool:
    """行がダミーパターンを含むか判定"""
    for pattern in DUMMY_PATTERNS:
        if pattern in line:
            return True
    return False


def main():
    print("=" * 60)
    print("03_前工程データ抽出")
    print(f"入力: {INPUT_CSV}")
    print(f"出力: {OUTPUT_CSV}")
    print("=" * 60)

    # 入力ファイル確認
    if not INPUT_CSV.exists():
        print(f"エラー: 入力ファイルが見つかりません: {INPUT_CSV}")
        return False

    # 出力ディレクトリ確認
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ファイル読み込み
    print("\nCSV読み込み中...")
    with open(INPUT_CSV, 'r', encoding='cp932') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"  総行数: {total_lines:,}行")

    # ヘッダー行を取得
    if total_lines == 0:
        print("エラー: ファイルが空です")
        return False

    header = lines[0]
    data_lines = lines[1:]

    print(f"  データ行数: {len(data_lines):,}行")

    # ダミーデータ除外
    print("\nダミーデータを除外中...")
    valid_lines = []
    dummy_count = 0

    for line in data_lines:
        if contains_dummy_pattern(line):
            dummy_count += 1
        else:
            valid_lines.append(line)

    print(f"  ダミーデータ（削除）: {dummy_count:,}行")
    print(f"  有効データ: {len(valid_lines):,}行")

    # 削除されたダミーデータのサンプル表示
    if dummy_count > 0:
        print(f"\nダミーデータ削除例（最初の3行）:")
        sample_count = 0
        for line in data_lines:
            if contains_dummy_pattern(line):
                # 最初の列（完成部番）を抽出して表示
                cols = line.split(',')
                if len(cols) > 1:
                    print(f"  - {cols[1].strip()}")
                sample_count += 1
                if sample_count >= 3:
                    break

    # 出力
    print(f"\n出力中: {OUTPUT_CSV}")
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(header)
        f.writelines(valid_lines)

    print(f"\n処理完了")
    print(f"  入力: {total_lines:,}行")
    print(f"  出力: {len(valid_lines) + 1:,}行（ヘッダー含む）")
    print(f"  削除: {dummy_count:,}行")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
