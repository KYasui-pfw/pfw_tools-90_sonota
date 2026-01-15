# -*- coding: utf-8 -*-
"""
再作成.csvのrBOMキーでlist.csvを検索し、1:複数マッチするケースを抽出
list.csv側のEJ発注番号が再作成.csvに存在するかチェック
"""

import pandas as pd
from pathlib import Path

# パス設定
BASE_DIR = Path(__file__).parent
LIST_CSV = BASE_DIR / "list.csv"
SAISAKU_CSV = BASE_DIR / "再作成.csv"
OUTPUT_CSV = BASE_DIR / "01_複数マッチ.csv"


def main():
    # list.csv読み込み
    list_df = pd.read_csv(LIST_CSV, encoding='utf-8-sig')
    print(f"list.csv 読み込み: {len(list_df)}行")

    # 再作成.csv読み込み
    saisaku_df = pd.read_csv(SAISAKU_CSV, encoding='utf-8-sig')
    print(f"再作成.csv 読み込み: {len(saisaku_df)}行")

    # 再作成.csvにキー列を作成（0埋め9桁+0埋め3桁）
    saisaku_df['rBOM発注番号+行番号'] = (
        saisaku_df['rBOM発注番号'].apply(lambda x: str(x).zfill(9))
        + '+'
        + saisaku_df['rBOM行番号'].apply(lambda x: str(x).zfill(3))
    )

    # 再作成.csvのユニークなrBOMキーを取得
    saisaku_keys = saisaku_df['rBOM発注番号+行番号'].unique()
    print(f"再作成.csv ユニークrBOMキー数: {len(saisaku_keys)}")

    # 再作成.csvのEJ発注番号セットを作成（存在チェック用）
    saisaku_ej_set = set(saisaku_df['EJ発注番号'].tolist())
    print(f"再作成.csv ユニークEJ発注番号数: {len(saisaku_ej_set)}")

    # 再作成.csvの全行について処理
    results = []
    for _, saisaku_row in saisaku_df.iterrows():
        key = saisaku_row['rBOM発注番号+行番号']

        # list.csvでマッチするレコードを検索
        matches = list_df[list_df['rBOM発注番号+行番号'] == key]

        ej_list = matches['EJ発注番号'].tolist() if len(matches) > 0 else []
        # 各EJ発注番号が再作成.csvに存在するかチェック
        exists_list = ['○' if ej in saisaku_ej_set else '×' for ej in ej_list]

        results.append({
            'EJ発注番号': saisaku_row['EJ発注番号'],
            'rBOM発注番号': saisaku_row['rBOM発注番号'],
            'rBOM行番号': saisaku_row['rBOM行番号'],
            'rBOM発注番号+行番号': key,
            'EJ仕入先コード': saisaku_row['EJ仕入先コード'],
            'rBOM仕入先コード': saisaku_row['rBOM仕入先コード'],
            'list.csvマッチ数': len(matches),
            'list.csv_EJ発注番号': ', '.join(ej_list),
            '再作成.csv存在': ', '.join(exists_list),
            '存在しないEJ発注番号': ', '.join([ej for ej, ex in zip(ej_list, exists_list) if ex == '×']),
        })

    print(f"\n出力件数: {len(results)}件")

    # DataFrame化して出力
    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values('rBOM発注番号+行番号')
    result_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"出力: {OUTPUT_CSV}")

    # マッチ数の分布
    if len(results) > 0:
        print("\n=== list.csvマッチ数の分布 ===")
        dist = result_df['list.csvマッチ数'].value_counts().sort_index()
        for cnt, num in dist.items():
            print(f"  {cnt}件マッチ: {num}行")

        # 存在しないEJ発注番号があるケースをカウント
        has_missing = result_df[result_df['存在しないEJ発注番号'] != '']
        print(f"\n再作成.csvに存在しないEJ発注番号があるケース: {len(has_missing)}件")

        if len(has_missing) > 0:
            print("\n=== 存在しないEJ発注番号の詳細 ===")
            for _, row in has_missing.iterrows():
                print(f"{row['rBOM発注番号+行番号']}: {row['list.csvマッチ数']}件 -> {row['list.csv_EJ発注番号']} ({row['再作成.csv存在']}) ★無し: {row['存在しないEJ発注番号']}")


if __name__ == "__main__":
    main()
