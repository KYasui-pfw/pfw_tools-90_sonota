# -*- coding: utf-8 -*-
"""
split_csv.py

調査用.csvを条件に基づいて4つのCSVに分割する

1. EJ発注番号が空欄ではなく、rBOM発注番号+行番号が空欄のデータ
2. EJ発注番号とrBOM発注番号+行番号の両方が空欄ではないデータと、
   そのrBOM発注番号+行番号と同じrBOM発注番号+行番号をもつデータ
3. rBOM発注番号+行番号が空欄ではなく、EJ発注番号が空欄のデータ
4. 上記1～3に当てはまらなかったデータ
"""

import os
import pandas as pd

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "調査用.csv")

# カラムインデックス（0始まり）
COL_EJ_ORDER = 1      # EJ発注番号
COL_RBOM_ORDER = 10   # rBOM発注番号+行番号


def main():
    print("=" * 60)
    print("CSV分割処理")
    print("=" * 60)
    print()

    # CSV読み込み
    print(f"入力ファイル: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, encoding="cp932", dtype=str)
    print(f"読み込み行数: {len(df)}")

    # カラム名取得
    cols = df.columns.tolist()
    print(f"カラム: {cols}")
    print()

    # カラム名を使いやすく
    ej_col = cols[COL_EJ_ORDER]
    rbom_col = cols[COL_RBOM_ORDER]
    print(f"EJ発注番号カラム: {ej_col}")
    print(f"rBOM発注番号+行番号カラム: {rbom_col}")
    print()

    # 空欄判定用の関数
    def is_empty(val):
        return pd.isna(val) or str(val).strip() == ""

    def is_not_empty(val):
        return not is_empty(val)

    # rBOM発注番号+行番号から発注番号部分（左側9桁）を抽出
    def extract_rbom_pono(val):
        if pd.isna(val) or str(val).strip() == "":
            return ""
        # +で区切られた左側を取得
        return str(val).split("+")[0]

    # 各行の状態を判定
    df["_ej_empty"] = df[ej_col].apply(is_empty)
    df["_rbom_empty"] = df[rbom_col].apply(is_empty)
    df["_rbom_pono"] = df[rbom_col].apply(extract_rbom_pono)

    # ========================================
    # 条件1: EJ発注番号あり、rBOM発注番号+行番号なし
    # ========================================
    cond1 = (~df["_ej_empty"]) & (df["_rbom_empty"])
    df1 = df[cond1].copy()
    print(f"条件1 (EJあり・rBOMなし): {len(df1)}件")

    # ========================================
    # 条件2: 両方ありのデータ + 同じrBOM発注番号を持つデータ
    # ========================================
    # まず両方ありのデータを抽出
    cond_both = (~df["_ej_empty"]) & (~df["_rbom_empty"])
    df_both = df[cond_both]

    # 両方ありのrBOM発注番号（+行番号ではなく発注番号のみ）のリスト
    rbom_pono_with_both = df_both["_rbom_pono"].unique().tolist()
    print(f"  両方ありのrBOM発注番号数: {len(rbom_pono_with_both)}")

    # 同じrBOM発注番号を持つデータ（条件1で使用済みは除く）
    cond2 = df["_rbom_pono"].isin(rbom_pono_with_both) & (~cond1)
    df2 = df[cond2].copy()
    print(f"条件2 (両方あり + 同一rBOM発注番号): {len(df2)}件")

    # ========================================
    # 条件3: rBOM発注番号+行番号あり、EJ発注番号なし
    # （条件2で使用済みは除く）
    # ========================================
    cond3 = (df["_ej_empty"]) & (~df["_rbom_empty"]) & (~cond2)
    df3 = df[cond3].copy()
    print(f"条件3 (EJなし・rBOMあり、条件2以外): {len(df3)}件")

    # ========================================
    # 条件4: 上記以外
    # ========================================
    cond4 = ~(cond1 | cond2 | cond3)
    df4 = df[cond4].copy()
    print(f"条件4 (その他): {len(df4)}件")

    # 合計確認
    total = len(df1) + len(df2) + len(df3) + len(df4)
    print()
    print(f"合計: {total}件 (元データ: {len(df)}件)")

    if total != len(df):
        print("警告: 合計が元データと一致しません")

    # 作業用カラムを削除
    for d in [df1, df2, df3, df4]:
        d.drop(columns=["_ej_empty", "_rbom_empty", "_rbom_pono"], inplace=True)

    # CSV出力
    print()
    print("CSV出力中...")

    output1 = os.path.join(SCRIPT_DIR, "01_EJあり_rBOMなし.csv")
    output2 = os.path.join(SCRIPT_DIR, "02_両方あり_同一rBOM.csv")
    output3 = os.path.join(SCRIPT_DIR, "03_EJなし_rBOMあり.csv")
    output4 = os.path.join(SCRIPT_DIR, "04_その他.csv")

    df1.to_csv(output1, index=False, encoding="cp932")
    df2.to_csv(output2, index=False, encoding="cp932")
    df3.to_csv(output3, index=False, encoding="cp932")
    df4.to_csv(output4, index=False, encoding="cp932")

    print(f"  {output1}: {len(df1)}件")
    print(f"  {output2}: {len(df2)}件")
    print(f"  {output3}: {len(df3)}件")
    print(f"  {output4}: {len(df4)}件")

    print()
    print("=" * 60)
    print("処理完了")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
