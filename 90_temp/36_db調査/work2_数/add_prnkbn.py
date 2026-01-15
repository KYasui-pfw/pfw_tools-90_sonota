# -*- coding: utf-8 -*-
"""
add_prnkbn.py

02_両方あり_同一rBOM.csvにD3330テーブルからPRNKBNを取得して追加する

キー: rBOM発注番号（rBOM発注番号+行番号の左側9桁）
"""

import os
import pandas as pd
import requests

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "02_両方あり_同一rBOM.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "02_両方あり_同一rBOM_PRNKBN.csv")

# API設定
API_BASE_URL = "http://pfw-api"
API_KEY = "oG5^Ls%#20yq"  # READ_API_KEY

# カラムインデックス（0始まり）
COL_RBOM_ORDER = 10   # rBOM発注番号+行番号


def query_d3330(pono_list):
    """
    D3330テーブルからPONO, PRNKBNを取得
    """
    url = f"{API_BASE_URL}/query"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "table": "D3330",
        "columns": ["PONO", "PRNKBN"],
        "where": {
            "or": [{"PONO": {"eq": pono}} for pono in pono_list]
        },
        "limit": 10000
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()


def main():
    print("=" * 60)
    print("D3330 PRNKBN取得処理")
    print("=" * 60)
    print()

    # CSV読み込み
    print(f"入力ファイル: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, encoding="cp932", dtype=str)
    print(f"読み込み行数: {len(df)}")

    # カラム名取得
    cols = df.columns.tolist()
    rbom_col = cols[COL_RBOM_ORDER]
    print(f"rBOM発注番号+行番号カラム: {rbom_col}")
    print()

    # rBOM発注番号（左側9桁）を抽出
    def extract_rbom_pono(val):
        if pd.isna(val) or str(val).strip() == "":
            return ""
        return str(val).split("+")[0]

    df["_rbom_pono"] = df[rbom_col].apply(extract_rbom_pono)

    # ユニークなrBOM発注番号リストを取得（空欄除く）
    pono_list = df[df["_rbom_pono"] != ""]["_rbom_pono"].unique().tolist()
    print(f"ユニークrBOM発注番号数: {len(pono_list)}")
    print()

    # D3330からデータ取得（バッチ処理）
    print("D3330からデータ取得中...")
    all_data = []
    batch_size = 100

    for i in range(0, len(pono_list), batch_size):
        batch = pono_list[i:i+batch_size]
        print(f"  バッチ {i//batch_size + 1}/{(len(pono_list)-1)//batch_size + 1}: {len(batch)}件...")

        try:
            result = query_d3330(batch)
            if "rows" in result:
                all_data.extend(result["rows"])
                print(f"    -> {len(result['rows'])}行取得")
            else:
                print(f"    -> データなし")
        except Exception as e:
            print(f"    -> エラー: {e}")

    print(f"合計取得行数: {len(all_data)}")
    print()

    # D3330データをDataFrameに変換
    if all_data:
        d3330_df = pd.DataFrame(all_data)
        d3330_df["PONO"] = d3330_df["PONO"].astype(str)
        # 重複があれば最初の値を使用
        d3330_df = d3330_df.drop_duplicates(subset=["PONO"], keep="first")
        print(f"ユニークPONO数: {len(d3330_df)}")
    else:
        d3330_df = pd.DataFrame(columns=["PONO", "PRNKBN"])

    # マージ
    df = df.merge(
        d3330_df[["PONO", "PRNKBN"]],
        left_on="_rbom_pono",
        right_on="PONO",
        how="left"
    )

    # 不要カラム削除
    df.drop(columns=["_rbom_pono", "PONO"], inplace=True)

    # 出力
    df.to_csv(OUTPUT_FILE, index=False, encoding="cp932")
    print()
    print(f"出力ファイル: {OUTPUT_FILE}")
    print(f"出力行数: {len(df)}")

    # 結果サマリー
    print()
    print("=" * 60)
    print("処理完了")
    print("=" * 60)
    prnkbn_counts = df["PRNKBN"].value_counts(dropna=False)
    print("PRNKBN分布:")
    for val, cnt in prnkbn_counts.items():
        print(f"  {val}: {cnt}件")

    return 0


if __name__ == "__main__":
    exit(main())
