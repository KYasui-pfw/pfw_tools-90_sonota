# -*- coding: utf-8 -*-
"""
01_複数マッチ.csvのrBOM発注番号+行番号でlist.csvを検索し、マッチ行数を調査
EJ発注番号+rBOM発注番号+行番号をキーにしてEJ数を取得
"""

import pandas as pd
from pathlib import Path

# パス設定
BASE_DIR = Path(__file__).parent
INPUT_CSV = BASE_DIR / "01_複数マッチ.csv"
LIST_CSV = BASE_DIR / "list.csv"
OUTPUT_CSV = BASE_DIR / "02_完納対象調査.csv"


def main():
    # 入力ファイル読み込み
    input_df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
    print(f"01_複数マッチ.csv 読み込み: {len(input_df)}行")

    list_df = pd.read_csv(LIST_CSV, encoding='utf-8-sig')
    print(f"list.csv 読み込み: {len(list_df)}行")

    # list.csvのrBOM発注番号+行番号でグループ化してカウント
    list_counts = list_df.groupby('rBOM発注番号+行番号').size().to_dict()

    # マッチ行数を取得
    input_df['list.csvマッチ行数'] = input_df['rBOM発注番号+行番号'].map(
        lambda x: list_counts.get(x, 0)
    )

    # rBOM発注番号+行番号の右に挿入（列の順序を調整）
    cols = input_df.columns.tolist()
    key_idx = cols.index('rBOM発注番号+行番号')
    # rBOM発注番号+行番号の直後に移動
    cols.remove('list.csvマッチ行数')
    cols.insert(key_idx + 1, 'list.csvマッチ行数')
    input_df = input_df[cols]

    # EJ発注番号+rBOM発注番号+行番号をキーにしてEJ数、EJ品目コード、発注担当者を取得
    list_df['_key'] = list_df['EJ発注番号'].astype(str) + '_' + list_df['rBOM発注番号+行番号'].astype(str)
    ej_qty_map = list_df.set_index('_key')['EJ数'].to_dict()
    ej_item_map = list_df.set_index('_key')['EJ品目コード'].to_dict()
    ej_person_map = list_df.set_index('_key')['発注担当者'].to_dict()

    input_df['_key'] = input_df['EJ発注番号'].astype(str) + '_' + input_df['rBOM発注番号+行番号'].astype(str)
    input_df['EJ数'] = input_df['_key'].map(lambda x: ej_qty_map.get(x, ''))
    input_df['EJ品目コード'] = input_df['_key'].map(lambda x: ej_item_map.get(x, ''))
    input_df['発注担当者'] = input_df['_key'].map(lambda x: ej_person_map.get(x, ''))
    input_df = input_df.drop(columns=['_key'])

    # 出力
    input_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n出力: {OUTPUT_CSV}")
    print(f"出力件数: {len(input_df)}件")

    # マッチ行数の分布
    print("\n=== list.csvマッチ行数の分布 ===")
    dist = input_df['list.csvマッチ行数'].value_counts().sort_index()
    for cnt, num in dist.items():
        print(f"  {cnt}行マッチ: {num}件")

    # EJ数取得状況
    ej_found = input_df[input_df['EJ数'] != '']
    print(f"\nEJ数取得: {len(ej_found)}件 / {len(input_df)}件")


if __name__ == "__main__":
    main()
