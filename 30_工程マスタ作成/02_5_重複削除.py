# -*- coding: utf-8 -*-
"""
02_5_重複削除.py
4-01 CAMKakouDenpyo_カム課付き.csv から不要な列を削除し、重複行を削除

削除対象列:
  - 梱包開始日、発行日、組立開始日、生産月次、伝票Ｎｏ
  - 必要数、未引当在庫数、手持ち在庫数、得意先注文番号、出庫済数

出力:
  - work/02_5_カム課データ_重複削除.csv
"""

import pandas as pd
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 入力ファイル
INPUT_CSV = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work\4-01 CAMKakouDenpyo_カム課付き.csv")

# 出力先
OUTPUT_DIR = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work")
OUTPUT_CSV = OUTPUT_DIR / "02_5_カム課データ_重複削除.csv"

# 削除対象列
DROP_COLUMNS = [
    "梱包開始日",
    "発行日",
    "組立開始日",
    "生産月次",
    "伝票Ｎｏ",
    "必要数",
    "未引当在庫数",
    "手持ち在庫数",
    "得意先注文番号",
    "出庫済数"
]


def main():
    print("=" * 60)
    print("02_5_重複削除")
    print(f"入力: {INPUT_CSV}")
    print(f"出力: {OUTPUT_CSV}")
    print("=" * 60)

    # 入力ファイル確認
    if not INPUT_CSV.exists():
        print(f"エラー: 入力ファイルが見つかりません: {INPUT_CSV}")
        return False

    # 出力ディレクトリ確認
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # CSV読み込み
    print("\nCSV読み込み中...")
    df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
    print(f"  元データ行数: {len(df)}")
    print(f"  元データ列数: {len(df.columns)}")

    # 元の列名表示
    print(f"\n元の列:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")

    # 削除対象列の確認
    existing_drop_cols = [col for col in DROP_COLUMNS if col in df.columns]
    missing_drop_cols = [col for col in DROP_COLUMNS if col not in df.columns]

    if existing_drop_cols:
        print(f"\n削除する列 ({len(existing_drop_cols)}個):")
        for col in existing_drop_cols:
            print(f"  - {col}")

    if missing_drop_cols:
        print(f"\n警告: 以下の列が見つかりません:")
        for col in missing_drop_cols:
            print(f"  - {col}")

    # 列を削除
    print("\n列を削除中...")
    df_filtered = df.drop(columns=existing_drop_cols)
    print(f"  削除後の列数: {len(df_filtered.columns)}")

    # 残った列名表示
    print(f"\n残った列:")
    for i, col in enumerate(df_filtered.columns, 1):
        print(f"  {i:2d}. {col}")

    # 加工部番ごとに1行に絞り込む
    print("\n加工部番ごとに1行に絞り込み中...")
    print(f"  絞り込み前: {len(df_filtered)}行")
    print(f"  加工部番ユニーク数: {df_filtered['加工部番'].nunique()}件")

    # 優先順位のランク付け
    def get_status_rank(status):
        """カム課_伝票データ有無の優先順位を数値化"""
        if status == "有り":
            return 1
        elif status == "子部番無し":
            return 2
        elif status == "在庫のため過去を検索":
            return 3
        else:
            return 4

    # 優先順位列を追加
    df_filtered['_priority_rank'] = df_filtered['カム課_伝票データ有無'].apply(get_status_rank)

    # カム課_月次をNaNを考慮して数値化（NaNは0として扱う）
    df_filtered['_month_value'] = pd.to_numeric(df_filtered['カム課_月次'], errors='coerce').fillna(0)

    # 元の行番号を保持（最後の優先順位用）
    df_filtered['_original_index'] = range(len(df_filtered))

    # ソート: 加工部番 → 優先順位ランク → 月次降順 → 元の行番号
    df_sorted = df_filtered.sort_values(
        by=['加工部番', '_priority_rank', '_month_value', '_original_index'],
        ascending=[True, True, False, True]
    )

    # 加工部番ごとに最初の行のみ取得
    df_unique = df_sorted.groupby('加工部番', as_index=False).first()

    # 作業用列を削除
    df_unique = df_unique.drop(columns=['_priority_rank', '_month_value', '_original_index'])

    duplicate_count = len(df_filtered) - len(df_unique)
    print(f"  絞り込み後: {len(df_unique)}行")
    print(f"  削除された重複行: {duplicate_count}行")

    # 優先順位の内訳を表示
    print(f"\n優先順位別の内訳:")
    status_counts = df_unique['カム課_伝票データ有無'].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count}件")

    # CSV出力
    print(f"\n出力中: {OUTPUT_CSV}")
    df_unique.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

    print(f"\n処理完了")
    print(f"  出力ファイル: {OUTPUT_CSV.name}")
    print(f"  出力行数: {len(df_unique)}行")
    print(f"  出力列数: {len(df_unique.columns)}列")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
