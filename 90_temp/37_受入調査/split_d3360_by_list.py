# -*- coding: utf-8 -*-
"""
split_d3360_by_list.py

D3360データをlist.csvのPONO+POLINENOと照合し、
一致するもの・一致しないものに振り分けて出力する
"""

import sys
import os
import pandas as pd

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_FILE = os.path.join(SCRIPT_DIR, "list.csv")
D3360_FILE = os.path.join(SCRIPT_DIR, "PFW.D3360.csv")

# 出力ファイル
OUTPUT_MATCH = os.path.join(SCRIPT_DIR, "D3360_listに一致.csv")
OUTPUT_NOT_MATCH = os.path.join(SCRIPT_DIR, "D3360_listに不一致.csv")


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 60)
    print("D3360データ振り分け処理")
    print("=" * 60)
    print()

    # ========================================
    # list.csv読み込み
    # ========================================
    print(f"list.csv読み込み: {LIST_FILE}")
    df_list = pd.read_csv(LIST_FILE, encoding="cp932", dtype=str)
    print(f"  行数: {len(df_list)}")

    # PONO, POLINENOを正規化（空白除去、ゼロ埋め）
    df_list["PONO"] = df_list["PONO"].str.strip().str.zfill(9)
    df_list["POLINENO"] = df_list["POLINENO"].str.strip().astype(int)

    # PONO+POLINENOのセットを作成
    list_keys = set(zip(df_list["PONO"], df_list["POLINENO"]))
    print(f"  ユニークPONO+POLINENO数: {len(list_keys)}")
    print()

    # ========================================
    # D3360読み込み
    # ========================================
    print(f"D3360読み込み: {D3360_FILE}")
    df_d3360 = pd.read_csv(D3360_FILE, encoding="cp932", dtype=str)
    print(f"  行数: {len(df_d3360)}")

    # PONO, POLINENOを正規化
    df_d3360["PONO"] = df_d3360["PONO"].str.strip().str.replace('"', '').str.zfill(9)
    df_d3360["POLINENO"] = df_d3360["POLINENO"].str.strip().str.replace('"', '').astype(int)
    print()

    # ========================================
    # 振り分け
    # ========================================
    print("振り分け処理中...")

    # D3360の各行がlist.csvに存在するかチェック
    df_d3360["_in_list"] = df_d3360.apply(
        lambda row: (row["PONO"], row["POLINENO"]) in list_keys,
        axis=1
    )

    # 一致するもの
    df_match = df_d3360[df_d3360["_in_list"]].copy()
    df_match.drop(columns=["_in_list"], inplace=True)

    # 一致しないもの
    df_not_match = df_d3360[~df_d3360["_in_list"]].copy()
    df_not_match.drop(columns=["_in_list"], inplace=True)

    print(f"  一致: {len(df_match)}件")
    print(f"  不一致: {len(df_not_match)}件")
    print(f"  合計: {len(df_match) + len(df_not_match)}件 (元: {len(df_d3360)}件)")
    print()

    # ========================================
    # CSV出力
    # ========================================
    print("CSV出力中...")

    df_match.to_csv(OUTPUT_MATCH, index=False, encoding="cp932")
    print(f"  {OUTPUT_MATCH}: {len(df_match)}件")

    df_not_match.to_csv(OUTPUT_NOT_MATCH, index=False, encoding="cp932")
    print(f"  {OUTPUT_NOT_MATCH}: {len(df_not_match)}件")

    print()
    print("=" * 60)
    print("処理完了")
    print("=" * 60)

    # サマリー表示
    print()
    print("【サマリー】")
    print(f"  list.csvのPONO+POLINENO数: {len(list_keys)}")
    print(f"  D3360総行数: {len(df_d3360)}")
    print(f"  → listに一致: {len(df_match)}件")
    print(f"  → listに不一致: {len(df_not_match)}件")

    # 不一致のユニークPONO+POLINENO数
    if len(df_not_match) > 0:
        not_match_keys = set(zip(df_not_match["PONO"], df_not_match["POLINENO"]))
        print(f"  不一致のユニークPONO+POLINENO数: {len(not_match_keys)}")

    return 0


if __name__ == "__main__":
    exit(main())
